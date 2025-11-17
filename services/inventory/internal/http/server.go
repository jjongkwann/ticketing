package http

import (
	"context"
	"fmt"
	"log"
	"net/http"

	"github.com/ticketing/inventory/internal/config"
)

type Server struct {
	server *http.Server
	cfg    *config.Config
}

func NewHTTPServer(cfg *config.Config) *Server {
	mux := http.NewServeMux()

	s := &Server{
		cfg: cfg,
		server: &http.Server{
			Addr:    fmt.Sprintf(":%s", cfg.HTTPPort),
			Handler: mux,
		},
	}

	// Health check endpoint
	mux.HandleFunc("/health", s.healthHandler)
	mux.HandleFunc("/ready", s.readyHandler)

	return s
}

func (s *Server) Start() error {
	log.Printf("Starting HTTP server on port %s", s.cfg.HTTPPort)
	return s.server.ListenAndServe()
}

func (s *Server) Shutdown(ctx context.Context) error {
	return s.server.Shutdown(ctx)
}

func (s *Server) healthHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("OK"))
}

func (s *Server) readyHandler(w http.ResponseWriter, r *http.Request) {
	// TODO: Check dependencies (DynamoDB, Redis)
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("READY"))
}
