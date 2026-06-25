import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Users, Briefcase, Calendar, Clock, AlertCircle, CheckCircle } from 'lucide-react'
import {
  BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import apiClient from '../../api/client'

const TYPE_LABEL = { OFF: '휴무', VAC: '휴가' }
const TYPE_STYLE = {
  OFF: { bg: '#EFF6FF', text: '#3B82F6' },
  VAC: { bg: '#ECFDF5', text: '#059669' },
}

function formatMD(dateStr) {
  const [, m, d] = dateStr.split('-')
  return `${parseInt(m)}/${parseInt(d)}`
}

function formatDateRange(start, end) {
  if (!start) return '-'
  if (start === end) return formatMD(start)
  return `${formatMD(start)}~${formatMD(end)}`
}

const KPICard = ({ icon: Icon, label, value, sub, color, bg }) => (
  <div
    className="bg-white rounded-2xl p-6 border border-slate-200 flex items-start gap-4"
    style={{ boxShadow: '0 4px 20px rgba(0,0,0,0.06)' }}
  >
    <div
      className="w-12 h-12 rounded-2xl flex items-center justify-center shrink-0"
      style={{ background: bg }}
    >
      <Icon size={22} style={{ color }} />
    </div>
    <div className="min-w-0">
      <div className="text-slate-500 text-sm mb-1">{label}</div>
      <div className="font-bold text-slate-800 leading-none" style={{ fontSize: 28 }}>
        {value}
      </div>
      {sub && <div className="text-xs text-slate-400 mt-1">{sub}</div>}
    </div>
  </div>
)

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const { day, count } = payload[0].payload
  return (
    <div style={{
      background: '#fff',
      border: '1px solid #E2E8F0',
      borderRadius: 12,
      padding: '8px 12px',
      fontSize: 12,
      boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
    }}>
      {day}요일: {count}명 근무
    </div>
  )
}

export default function DashboardPage() {
  const [dashboard, setDashboard]         = useState(null)
  const [recentRequests, setRecentRequests] = useState([])
  const [isConfirmed, setIsConfirmed]     = useState(false)
  const [toast, setToast]                 = useState(null)

  const fetchDashboard = async () => {
    try {
      const { data } = await apiClient.get('/admin/dashboard')
      setDashboard(data)
    } catch {
      showToast('대시보드 데이터를 불러오지 못했습니다', false)
    }
  }

  const fetchRecentRequests = async () => {
    try {
      const { data } = await apiClient.get('/admin/requests', { params: { status: 'pending' } })
      setRecentRequests(data.slice(0, 5))
    } catch {
      // 실패해도 대시보드는 계속 표시
    }
  }

  const fetchScheduleStatus = async () => {
    try {
      const now = new Date()
      const { data } = await apiClient.get('/schedules', {
        params: { year: now.getFullYear(), month: now.getMonth() + 1 },
      })
      setIsConfirmed(data?.period_status === 'confirmed')
    } catch {
      // schedule period 없으면 미확정 상태로 표시
    }
  }

  useEffect(() => {
    fetchDashboard()
    fetchRecentRequests()
    fetchScheduleStatus()
  }, [])

  const showToast = (msg, ok = true) => {
    setToast({ msg, ok })
    setTimeout(() => setToast(null), 3000)
  }

  const handleQuickApprove = async (req) => {
    try {
      await apiClient.patch(`/admin/requests/${req.request_id}/approve`, { admin_comment: null })
      setRecentRequests((prev) => prev.filter((r) => r.request_id !== req.request_id))
      showToast(req.type === 'VAC'
        ? '휴가 신청이 승인되었습니다 (근무표에 VAC가 자동 배정되었습니다)'
        : '휴무 신청이 승인되었습니다')
      fetchDashboard()
    } catch (err) {
      showToast(err.response?.data?.detail ?? '승인에 실패했습니다', false)
    }
  }

  const handleQuickReject = async (req) => {
    try {
      await apiClient.patch(`/admin/requests/${req.request_id}/reject`, { admin_comment: '관리자 반려' })
      setRecentRequests((prev) => prev.filter((r) => r.request_id !== req.request_id))
      showToast('신청이 반려되었습니다')
      fetchDashboard()
    } catch (err) {
      showToast(err.response?.data?.detail ?? '반려에 실패했습니다', false)
    }
  }

  if (!dashboard) {
    return <div className="text-center py-20 text-slate-400 text-sm">불러오는 중...</div>
  }

  const {
    total_employees,
    today_working,
    today_on_leave,
    pending_requests,
    this_week_schedule,
  } = dashboard

  const now = new Date()
  const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토']
  const todayLabel = `${now.getFullYear()}년 ${now.getMonth() + 1}월 ${now.getDate()}일 (${WEEKDAYS[now.getDay()]})`
  const todayStr = now.toISOString().slice(0, 10)

  return (
    <div className="space-y-6">

      {toast && (
        <div
          className="fixed top-5 right-5 z-50 flex items-center gap-2 px-4 py-3 rounded-xl shadow-lg text-sm font-medium"
          style={{
            background: toast.ok ? '#ECFDF5' : '#FEF2F2',
            color:      toast.ok ? '#059669' : '#DC2626',
            border:     `1px solid ${toast.ok ? '#A7F3D0' : '#FECACA'}`,
          }}
        >
          {toast.ok ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          {toast.msg}
        </div>
      )}

      <div>
        <h1 className="font-bold text-slate-800" style={{ fontSize: 24 }}>
          관리자 대시보드
        </h1>
        <p className="text-slate-500 text-sm mt-0.5">
          {todayLabel} · 오늘의 근무 현황
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          icon={Users}    label="전체 직원 수"
          value={total_employees} sub="활성 직원 기준"
          color="#3B82F6" bg="#EFF6FF"
        />
        <KPICard
          icon={Briefcase} label="오늘 근무자"
          value={today_working} sub="is_work_day 기준"
          color="#8B5CF6" bg="#F5F3FF"
        />
        <KPICard
          icon={Calendar} label="오늘 휴가자"
          value={today_on_leave} sub="VAC 코드 기준"
          color="#10B981" bg="#ECFDF5"
        />
        <KPICard
          icon={Clock} label="승인 대기"
          value={pending_requests} sub="처리 필요한 요청"
          color="#F59E0B" bg="#FEF3C7"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">

        <div
          className="lg:col-span-3 bg-white rounded-2xl p-6 border border-slate-200"
          style={{ boxShadow: '0 4px 20px rgba(0,0,0,0.06)' }}
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="font-semibold text-slate-800" style={{ fontSize: 16 }}>
                이번 주 근무자 수
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                {this_week_schedule[0]?.date} ~ {this_week_schedule[6]?.date}
              </p>
            </div>
            <div className="flex items-center gap-3 text-xs text-slate-400">
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-sm" style={{ background: '#3B82F6' }} />
                일반
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-sm" style={{ background: '#8B5CF6' }} />
                오늘
              </div>
            </div>
          </div>

          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={this_week_schedule} barSize={28}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
              <XAxis
                dataKey="day"
                tick={{ fontSize: 12, fill: '#94A3B8' }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 12, fill: '#94A3B8' }}
                axisLine={false}
                tickLine={false}
                width={24}
                allowDecimals={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {this_week_schedule.map((entry) => (
                  <Cell
                    key={entry.date}
                    fill={entry.date === todayStr ? '#8B5CF6' : '#3B82F6'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div
          className="lg:col-span-2 bg-white rounded-2xl p-6 border border-slate-200"
          style={{ boxShadow: '0 4px 20px rgba(0,0,0,0.06)' }}
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-slate-800" style={{ fontSize: 16 }}>최근 요청</h2>
            <Link
              to="/admin/requests"
              className="text-xs text-blue-500 hover:text-blue-600 transition-colors"
            >
              전체 보기 →
            </Link>
          </div>

          {recentRequests.length === 0 ? (
            <p className="text-sm text-slate-400 text-center py-8">대기 중인 요청이 없습니다</p>
          ) : (
            <div className="space-y-3">
              {recentRequests.map((req) => {
                const ts = TYPE_STYLE[req.type] ?? TYPE_STYLE.OFF
                return (
                  <div key={req.request_id} className="flex items-center gap-3">
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0"
                      style={{ background: '#3B82F6' }}
                    >
                      {req.requester_name?.charAt(0) ?? '?'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-medium text-slate-700 truncate">
                          {req.requester_name}
                        </span>
                        <span
                          className="text-xs px-1.5 py-0.5 rounded-full shrink-0"
                          style={{ background: ts.bg, color: ts.text }}
                        >
                          {TYPE_LABEL[req.type]}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 mt-0.5">
                        {formatDateRange(req.start_date, req.end_date)}
                      </div>
                    </div>
                    <div className="flex gap-1 shrink-0">
                      <button
                        onClick={() => handleQuickApprove(req)}
                        className="px-2 py-1 rounded-lg text-xs font-medium text-white"
                        style={{ background: '#3B82F6' }}
                      >
                        승인
                      </button>
                      <button
                        onClick={() => handleQuickReject(req)}
                        className="px-2 py-1 rounded-lg text-xs font-medium text-white"
                        style={{ background: '#EF4444' }}
                      >
                        반려
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {pending_requests > 0 && (
          <div
            className="flex items-start gap-3 p-4 rounded-2xl border"
            style={{ background: '#FFFBEB', borderColor: '#FDE68A' }}
          >
            <AlertCircle size={18} style={{ color: '#D97706' }} className="shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium" style={{ color: '#92400E' }}>
                승인 대기 요청 알림
              </p>
              <p className="text-xs mt-0.5" style={{ color: '#B45309' }}>
                처리 대기 중인 요청이 {pending_requests}건 있습니다. 요청 관리 화면에서 확인해주세요.
              </p>
            </div>
          </div>
        )}

        <div
          className="flex items-start gap-3 p-4 rounded-2xl border"
          style={isConfirmed
            ? { background: '#EFF6FF', borderColor: '#BFDBFE' }
            : { background: '#ECFDF5', borderColor: '#A7F3D0' }}
        >
          <CheckCircle
            size={18}
            style={{ color: isConfirmed ? '#3B82F6' : '#059669' }}
            className="shrink-0 mt-0.5"
          />
          <div>
            <p className="text-sm font-medium" style={{ color: isConfirmed ? '#1E40AF' : '#065F46' }}>
              근무표 상태
            </p>
            <p className="text-xs mt-0.5" style={{ color: isConfirmed ? '#1D4ED8' : '#047857' }}>
              {isConfirmed
                ? '이번 달 근무표가 확정되었습니다.'
                : '근무표 작성 완료 후 확정 처리를 해주세요.'}
            </p>
          </div>
        </div>
      </div>

    </div>
  )
}
