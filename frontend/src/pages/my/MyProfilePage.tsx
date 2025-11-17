import { useState } from 'react'
import { useAuthStore } from '../../store/authStore'
import { useForm } from 'react-hook-form'

interface ProfileForm {
  name: string
  phone: string
  currentPassword?: string
  newPassword?: string
  confirmPassword?: string
}

export default function MyProfilePage() {
  const { user } = useAuthStore()
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ProfileForm>({
    defaultValues: {
      name: user?.name || '',
      phone: user?.phone || '',
    },
  })

  const newPassword = watch('newPassword')

  const onSubmit = async (_data: ProfileForm) => {
    setIsSaving(true)
    try {
      // TODO: Call API to update profile
      await new Promise((resolve) => setTimeout(resolve, 1000))
      alert('프로필이 업데이트되었습니다.')
      setIsEditing(false)
    } catch (error) {
      alert('업데이트에 실패했습니다.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="bg-gray-50 min-h-screen py-8">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">프로필 설정</h1>

        {/* Profile Card */}
        <div className="bg-white rounded-lg shadow-sm p-8 mb-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold">기본 정보</h2>
            {!isEditing && (
              <button
                onClick={() => setIsEditing(true)}
                className="btn btn-outline"
              >
                수정하기
              </button>
            )}
          </div>

          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-6">
              {/* Email (Read-only) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  이메일
                </label>
                <input
                  type="email"
                  value={user?.email}
                  disabled
                  className="input bg-gray-100"
                />
                <p className="mt-1 text-xs text-gray-500">이메일은 변경할 수 없습니다</p>
              </div>

              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  이름
                </label>
                <input
                  type="text"
                  className="input"
                  disabled={!isEditing}
                  {...register('name', { required: '이름을 입력해주세요' })}
                />
                {errors.name && (
                  <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
                )}
              </div>

              {/* Phone */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  전화번호
                </label>
                <input
                  type="tel"
                  className="input"
                  disabled={!isEditing}
                  {...register('phone', {
                    required: '전화번호를 입력해주세요',
                    pattern: {
                      value: /^01[0-9]-?[0-9]{4}-?[0-9]{4}$/,
                      message: '올바른 전화번호 형식이 아닙니다',
                    },
                  })}
                />
                {errors.phone && (
                  <p className="mt-1 text-sm text-red-600">{errors.phone.message}</p>
                )}
              </div>

              {/* Verified Fan Badge */}
              {user?.verified_fan_tier && (
                <div className="bg-primary-50 border border-primary-200 rounded-lg p-4">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">✅</span>
                    <div>
                      <div className="font-bold text-primary-900">
                        Verified Fan - {user.verified_fan_tier.toUpperCase()}
                      </div>
                      <div className="text-sm text-primary-700">
                        우선 구매 및 특별 혜택 제공
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {isEditing && (
              <div className="mt-8 pt-8 border-t">
                <h3 className="text-lg font-bold mb-4">비밀번호 변경</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      현재 비밀번호
                    </label>
                    <input
                      type="password"
                      className="input"
                      {...register('currentPassword')}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      새 비밀번호
                    </label>
                    <input
                      type="password"
                      className="input"
                      {...register('newPassword', {
                        minLength: {
                          value: 8,
                          message: '비밀번호는 최소 8자 이상이어야 합니다',
                        },
                      })}
                    />
                    {errors.newPassword && (
                      <p className="mt-1 text-sm text-red-600">{errors.newPassword.message}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      새 비밀번호 확인
                    </label>
                    <input
                      type="password"
                      className="input"
                      {...register('confirmPassword', {
                        validate: (value) =>
                          !newPassword || value === newPassword || '비밀번호가 일치하지 않습니다',
                      })}
                    />
                    {errors.confirmPassword && (
                      <p className="mt-1 text-sm text-red-600">
                        {errors.confirmPassword.message}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {isEditing && (
              <div className="mt-8 flex gap-4">
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="flex-1 btn btn-outline"
                >
                  취소
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="flex-1 btn btn-primary"
                >
                  {isSaving ? '저장 중...' : '저장하기'}
                </button>
              </div>
            )}
          </form>
        </div>

        {/* Notification Settings */}
        <div className="bg-white rounded-lg shadow-sm p-8">
          <h2 className="text-xl font-bold mb-6">알림 설정</h2>
          <div className="space-y-4">
            <label className="flex items-center justify-between">
              <span className="text-gray-700">이메일 알림</span>
              <input type="checkbox" className="toggle" defaultChecked />
            </label>
            <label className="flex items-center justify-between">
              <span className="text-gray-700">SMS 알림</span>
              <input type="checkbox" className="toggle" defaultChecked />
            </label>
            <label className="flex items-center justify-between">
              <span className="text-gray-700">마케팅 수신 동의</span>
              <input type="checkbox" className="toggle" />
            </label>
          </div>
        </div>
      </div>
    </div>
  )
}
