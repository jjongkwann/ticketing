package grpc

import (
	"context"
	"fmt"
	"log"
	"net"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"

	"github.com/ticketing/inventory/internal/config"
	"github.com/ticketing/inventory/internal/models"
	"github.com/ticketing/inventory/internal/service"
	pb "github.com/ticketing/inventory/proto"
)

type Server struct {
	pb.UnimplementedInventoryServiceServer
	service *service.InventoryService
	cfg     *config.Config
}

func NewGRPCServer(svc *service.InventoryService, cfg *config.Config) *Server {
	return &Server{
		service: svc,
		cfg:     cfg,
	}
}

func (s *Server) Start() error {
	lis, err := net.Listen("tcp", fmt.Sprintf(":%s", s.cfg.GRPCPort))
	if err != nil {
		return fmt.Errorf("failed to listen: %w", err)
	}

	grpcServer := grpc.NewServer()
	pb.RegisterInventoryServiceServer(grpcServer, s)

	log.Printf("Starting gRPC server on port %s", s.cfg.GRPCPort)
	return grpcServer.Serve(lis)
}

// GetSeats implements the GetSeats RPC
func (s *Server) GetSeats(ctx context.Context, req *pb.GetSeatsRequest) (*pb.GetSeatsResponse, error) {
	var statusFilter *models.SeatStatus
	// If status filter is provided and not default (0), use it
	if req.StatusFilter != 0 {
		status := convertSeatStatus(req.StatusFilter)
		statusFilter = &status
	}

	seats, err := s.service.GetSeats(ctx, req.EventId, statusFilter, req.Limit)
	if err != nil {
		return nil, status.Errorf(codes.Internal, "failed to get seats: %v", err)
	}

	pbSeats := make([]*pb.Seat, len(seats))
	for i, seat := range seats {
		pbSeats[i] = convertSeatToProto(seat)
	}

	return &pb.GetSeatsResponse{
		Seats:   pbSeats,
		HasMore: false, // TODO: Implement pagination
	}, nil
}

// ReserveSeat implements the ReserveSeat RPC
func (s *Server) ReserveSeat(ctx context.Context, req *pb.ReserveSeatRequest) (*pb.ReserveSeatResponse, error) {
	reservationID, err := s.service.ReserveSeat(ctx, req.EventId, req.SeatNumber, req.UserId)
	if err != nil {
		return &pb.ReserveSeatResponse{
			Success: false,
			Message: err.Error(),
		}, nil
	}

	// Get the reserved seat
	seats, err := s.service.GetSeats(ctx, req.EventId, nil, 1000)
	if err != nil {
		return nil, status.Errorf(codes.Internal, "failed to get seat: %v", err)
	}

	var reservedSeat *models.Seat
	for _, seat := range seats {
		if seat.SeatNumber == req.SeatNumber {
			reservedSeat = seat
			break
		}
	}

	if reservedSeat == nil {
		return nil, status.Errorf(codes.NotFound, "seat not found")
	}

	return &pb.ReserveSeatResponse{
		Success:       true,
		Message:       "Seat reserved successfully",
		Seat:          convertSeatToProto(reservedSeat),
		ReservationId: reservationID,
	}, nil
}

// ReleaseSeat implements the ReleaseSeat RPC
func (s *Server) ReleaseSeat(ctx context.Context, req *pb.ReleaseSeatRequest) (*pb.ReleaseSeatResponse, error) {
	err := s.service.ReleaseSeat(ctx, req.EventId, req.SeatNumber, req.UserId)
	if err != nil {
		return &pb.ReleaseSeatResponse{
			Success: false,
			Message: err.Error(),
		}, nil
	}

	return &pb.ReleaseSeatResponse{
		Success: true,
		Message: "Seat released successfully",
	}, nil
}

// ConfirmBooking implements the ConfirmBooking RPC
func (s *Server) ConfirmBooking(ctx context.Context, req *pb.ConfirmBookingRequest) (*pb.ConfirmBookingResponse, error) {
	bookingID, err := s.service.ConfirmBooking(ctx, req.ReservationId, req.UserId, req.PaymentId)
	if err != nil {
		return &pb.ConfirmBookingResponse{
			Success: false,
			Message: err.Error(),
		}, nil
	}

	return &pb.ConfirmBookingResponse{
		Success:   true,
		Message:   "Booking confirmed successfully",
		BookingId: bookingID,
	}, nil
}

// CancelBooking implements the CancelBooking RPC
func (s *Server) CancelBooking(ctx context.Context, req *pb.CancelBookingRequest) (*pb.CancelBookingResponse, error) {
	// TODO: Implement cancel booking
	return &pb.CancelBookingResponse{
		Success: false,
		Message: "Not implemented",
	}, nil
}

// InitializeSeats implements the InitializeSeats RPC
func (s *Server) InitializeSeats(ctx context.Context, req *pb.InitializeSeatsRequest) (*pb.InitializeSeatsResponse, error) {
	count, err := s.service.InitializeSeats(ctx, req.EventId, int(req.TotalSeats), req.Price)
	if err != nil {
		return &pb.InitializeSeatsResponse{
			Success: false,
			Message: err.Error(),
		}, nil
	}

	return &pb.InitializeSeatsResponse{
		Success:      true,
		Message:      "Seats initialized successfully",
		CreatedCount: int32(count),
	}, nil
}

// Helper functions
func convertSeatStatus(status pb.SeatStatus) models.SeatStatus {
	switch status {
	case pb.SeatStatus_AVAILABLE:
		return models.SeatStatusAvailable
	case pb.SeatStatus_RESERVED:
		return models.SeatStatusReserved
	case pb.SeatStatus_BOOKED:
		return models.SeatStatusBooked
	default:
		return models.SeatStatusAvailable
	}
}

func convertSeatToProto(seat *models.Seat) *pb.Seat {
	var status pb.SeatStatus
	switch seat.Status {
	case models.SeatStatusAvailable:
		status = pb.SeatStatus_AVAILABLE
	case models.SeatStatusReserved:
		status = pb.SeatStatus_RESERVED
	case models.SeatStatusBooked:
		status = pb.SeatStatus_BOOKED
	}

	return &pb.Seat{
		EventId:    seat.EventID,
		SeatNumber: seat.SeatNumber,
		Status:     status,
		UserId:     seat.UserID,
		Price:      seat.Price,
		ReservedAt: seat.ReservedAt,
		Version:    int32(seat.Version),
	}
}
