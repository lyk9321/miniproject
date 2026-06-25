import { useState, useEffect } from 'react'
import { formatDistanceToNow } from 'date-fns'
import { ko } from 'date-fns/locale'
import { RefreshCw, CheckCircle, AlertCircle, ChevronDown } from 'lucide-react'
import apiClient from '../../api/client'

const STATUS_CONFIG = {
  pending:  { label: '대기 중', bg: '#FEF3C7', text: '#D97706' },
  approved: { label: '승인됨',  bg: '#ECFDF5', text: '#059669' },
  rejected: { label: '반려됨',  bg: '#FEF2F2', text: '#DC2626' },
  accepted: { label: '합의됨',  bg: '#EFF6FF', text: '#3B82F6' },
  expired:  { label: '만료됨',  bg: '#F8FAFC', text: '#94A3B8' },
}

const TYPE_CONFIG = {
  OFF: { label: '휴무', bg: '#EFF6FF', text: '#3B82F6' },
  VAC: { label: '휴가', bg: '#ECFDF5', text: '#059669' },
}

const STATUS_TABS = [
  { key: 'pending',  label: '대기 중' },
  { key: 'approved', label: '승인됨' },
  { key: 'rejected', label: '반려됨' },
  { key: '',         label: '전체' },
]

const TYPE_OPTIONS = [
  { value: '',     label: '전체' },
  { value: 'OFF',  label: '휴무 (OFF)' },
  { value: 'VAC',  label: '휴가 (VAC)' },
  { value: 'SWAP', label: '교대 요청' },
]

function formatMD(dateStr) {
  const [, m, d] = dateStr.split('-')
  return `${parseInt(m)}/${parseInt(d)}`
}

function formatDateRange(start, end) {
  if (!start) return '-'
  if (start === end) return formatMD(start)
  return `${formatMD(start)}~${formatMD(end)}`
}

export default function AdminRequestsPage() {
  const [activeStatus, setActiveStatus] = useState('pending')
  const [typeFilter, setTypeFilter]     = useState('')
  const [showTypeDropdown, setShowTypeDropdown] = useState(false)

  const [timeOffList, setTimeOffList] = useState([])
  const [swapList, setSwapList]       = useState([])

  const [detailItem, setDetailItem]     = useState(null)
  const [adminComment, setAdminComment] = useState('')

  const [swapApproveTarget, setSwapApproveTarget] = useState(null)

  const [swapRejectTarget, setSwapRejectTarget] = useState(null)
  const [swapRejectReason, setSwapRejectReason] = useState('')

  const [toast, setToast] = useState(null)

  const fetchAll = async () => {
    try {
      const [toRes, swapRes] = await Promise.all([
        apiClient.get('/admin/requests'),
        apiClient.get('/swap-requests'),
      ])
      setTimeOffList(toRes.data)
      setSwapList(swapRes.data)
    } catch {
      showToast('목록을 불러오지 못했습니다', false)
    }
  }

  useEffect(() => { fetchAll() }, [])

  const showToast = (msg, ok = true) => {
    setToast({ msg, ok })
    setTimeout(() => setToast(null), 3000)
  }

  const filteredTimeOff = timeOffList.filter((r) => {
    const matchStatus = activeStatus === '' || r.status === activeStatus
    const matchType   = typeFilter === '' || typeFilter === 'SWAP'
      ? typeFilter !== 'SWAP'
      : r.type === typeFilter
    return matchStatus && matchType
  })

  const filteredSwap = swapList.filter((r) => {
    const matchStatus = activeStatus === ''
      || r.status === activeStatus
      || (activeStatus === 'pending' && r.status === 'accepted')
    const showSwap    = typeFilter === '' || typeFilter === 'SWAP'
    return matchStatus && showSwap
  })

  const pendingTimeOff = timeOffList.filter((r) => r.status === 'pending').length
  const pendingSwap    = swapList.filter((r) => ['pending', 'accepted'].includes(r.status)).length
  const pendingTotal   = pendingTimeOff + pendingSwap

  const tabCounts = {
    pending:  pendingTotal,
    approved: timeOffList.filter((r) => r.status === 'approved').length,
    rejected: timeOffList.filter((r) => r.status === 'rejected').length,
    '':       timeOffList.length + swapList.length,
  }

  const handleApprove = async (item) => {
    try {
      await apiClient.patch(`/admin/requests/${item.request_id}/approve`, {
        admin_comment: adminComment || null,
      })
      setDetailItem(null)
      setAdminComment('')
      showToast(item.type === 'VAC'
        ? '휴가 신청이 승인되었습니다 (근무표에 VAC가 자동 배정되었습니다)'
        : '휴무 신청이 승인되었습니다')
      fetchAll()
    } catch (err) {
      showToast(err.response?.data?.detail ?? '승인에 실패했습니다', false)
    }
  }

  const handleReject = async (item) => {
    if (!adminComment.trim()) {
      showToast('반려 사유를 입력해주세요', false)
      return
    }
    try {
      await apiClient.patch(`/admin/requests/${item.request_id}/reject`, {
        admin_comment: adminComment,
      })
      setDetailItem(null)
      setAdminComment('')
      showToast('신청이 반려되었습니다')
      fetchAll()
    } catch (err) {
      showToast(err.response?.data?.detail ?? '반려에 실패했습니다', false)
    }
  }

  const openDetail = (item) => {
    setDetailItem(item)
    setAdminComment('')
  }

  const confirmSwapApprove = async () => {
    const req = swapApproveTarget
    try {
      await apiClient.patch(`/admin/swap-requests/${req.swap_request_id}/approve`)
      setSwapApproveTarget(null)
      showToast('교대 신청이 최종 승인되었습니다')
      fetchAll()
    } catch (err) {
      if (err?.response?.status === 409) {
        showToast('처리 중 충돌이 발생했습니다. 다시 시도해 주세요', false)
      } else {
        showToast(err.response?.data?.detail ?? '오류가 발생했습니다', false)
      }
      setSwapApproveTarget(null)
    }
  }

  const confirmSwapReject = async () => {
    if (!swapRejectReason.trim()) {
      showToast('반려 사유를 입력해주세요', false)
      return
    }
    const req = swapRejectTarget
    try {
      await apiClient.patch(`/admin/swap-requests/${req.swap_request_id}/reject`, {
        admin_comment: swapRejectReason,
      })
      setSwapRejectTarget(null)
      setSwapRejectReason('')
      showToast('교대 신청이 반려되었습니다')
      fetchAll()
    } catch (err) {
      showToast(err.response?.data?.detail ?? '반려에 실패했습니다', false)
    }
  }

  const showOnlySwap = typeFilter === 'SWAP'
  const showOnlyOff  = typeFilter !== '' && typeFilter !== 'SWAP'
  const totalCount   = showOnlySwap
    ? filteredSwap.length
    : showOnlyOff
      ? filteredTimeOff.length
      : filteredTimeOff.length + filteredSwap.length

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

      {swapApproveTarget && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-2xl p-6 w-[400px] shadow-xl">
            <h3 className="font-semibold text-slate-800 mb-2" style={{ fontSize: 16 }}>
              교대 최종 승인
            </h3>
            <p className="text-sm text-slate-600 mb-1">
              {swapApproveTarget.requester_name} {swapApproveTarget.shift_code} ↕{' '}
              {swapApproveTarget.proposer_name} {swapApproveTarget.proposer_shift_code}
            </p>
            <p className="text-sm font-medium text-slate-700 mb-6">
              이 교대를 최종 승인하시겠습니까?
            </p>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => setSwapApproveTarget(null)}
                className="px-4 py-2 rounded-lg text-sm text-slate-500 hover:bg-slate-100 transition-colors"
              >
                취소
              </button>
              <button
                onClick={confirmSwapApprove}
                className="px-4 py-2 rounded-lg text-sm font-medium text-white"
                style={{ background: '#3B82F6' }}
              >
                최종 승인
              </button>
            </div>
          </div>
        </div>
      )}

      {swapRejectTarget && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-2xl p-6 w-[400px] shadow-xl">
            <h3 className="font-semibold text-slate-800 mb-4" style={{ fontSize: 16 }}>
              교대 반려
            </h3>
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                반려 사유 (필수)
              </label>
              <textarea
                value={swapRejectReason}
                onChange={(e) => setSwapRejectReason(e.target.value)}
                placeholder="반려 사유를 입력해주세요"
                rows={3}
                className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm text-slate-700 focus:outline-none focus:border-blue-400 resize-none"
              />
            </div>
            <div className="flex gap-2 justify-end">
              <button
                onClick={() => { setSwapRejectTarget(null); setSwapRejectReason('') }}
                className="px-4 py-2 rounded-lg text-sm text-slate-500 hover:bg-slate-100 transition-colors"
              >
                취소
              </button>
              <button
                onClick={confirmSwapReject}
                className="px-4 py-2 rounded-lg text-sm font-medium text-white"
                style={{ background: '#EF4444' }}
              >
                반려 확정
              </button>
            </div>
          </div>
        </div>
      )}

      {detailItem && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-2xl p-6 w-[480px] shadow-xl">
            <h3 className="font-semibold text-slate-800 mb-4" style={{ fontSize: 16 }}>
              요청 상세
            </h3>

            <div className="space-y-3 mb-5 p-4 bg-slate-50 rounded-xl text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">신청자</span>
                <span className="font-medium text-slate-800">{detailItem.requester_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">유형</span>
                <span
                  className="text-xs font-medium px-2.5 py-1 rounded-full"
                  style={{ background: TYPE_CONFIG[detailItem.type]?.bg, color: TYPE_CONFIG[detailItem.type]?.text }}
                >
                  {TYPE_CONFIG[detailItem.type]?.label ?? detailItem.type}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">기간</span>
                <span className="font-medium text-slate-800">
                  {formatDateRange(detailItem.start_date, detailItem.end_date)}
                </span>
              </div>
              {detailItem.reason && (
                <div className="flex justify-between">
                  <span className="text-slate-500">사유</span>
                  <span className="text-slate-700 text-right max-w-[260px]">{detailItem.reason}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-slate-500">상태</span>
                <span
                  className="text-xs font-medium px-2.5 py-1 rounded-full"
                  style={{ background: STATUS_CONFIG[detailItem.status]?.bg, color: STATUS_CONFIG[detailItem.status]?.text }}
                >
                  {STATUS_CONFIG[detailItem.status]?.label}
                </span>
              </div>
              {detailItem.admin_comment && (
                <div className="flex justify-between">
                  <span className="text-slate-500">관리자 코멘트</span>
                  <span className="text-slate-700 text-right max-w-[260px]">{detailItem.admin_comment}</span>
                </div>
              )}
            </div>

            {detailItem.status === 'pending' ? (
              <>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    관리자 코멘트 (반려 시 필수)
                  </label>
                  <textarea
                    value={adminComment}
                    onChange={(e) => setAdminComment(e.target.value)}
                    placeholder="승인/반려 사유를 입력해주세요"
                    rows={3}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 text-sm text-slate-700 focus:outline-none focus:border-blue-400 resize-none"
                  />
                </div>
                <div className="flex gap-2 justify-end">
                  <button
                    onClick={() => setDetailItem(null)}
                    className="px-4 py-2 rounded-lg text-sm text-slate-500 hover:bg-slate-100 transition-colors"
                  >
                    닫기
                  </button>
                  <button
                    onClick={() => handleReject(detailItem)}
                    className="px-4 py-2 rounded-lg text-sm font-medium text-white"
                    style={{ background: '#EF4444' }}
                  >
                    반려
                  </button>
                  <button
                    onClick={() => handleApprove(detailItem)}
                    className="px-4 py-2 rounded-lg text-sm font-medium text-white"
                    style={{ background: '#3B82F6' }}
                  >
                    승인
                  </button>
                </div>
              </>
            ) : (
              <div className="flex justify-end">
                <button
                  onClick={() => setDetailItem(null)}
                  className="px-4 py-2 rounded-lg text-sm text-slate-500 hover:bg-slate-100 transition-colors"
                >
                  닫기
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      <div>
        <h1 className="font-bold text-slate-800" style={{ fontSize: 24 }}>요청 관리</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          휴무·휴가·교대 요청을 검토하고 승인 또는 반려합니다.
        </p>
      </div>

      <div className="flex gap-0 border-b border-slate-200">
        {STATUS_TABS.map((tab) => {
          const count = tabCounts[tab.key] ?? 0
          const active = activeStatus === tab.key
          return (
            <button
              key={tab.key}
              onClick={() => setActiveStatus(tab.key)}
              className="flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors"
              style={{
                borderColor: active ? '#3B82F6' : 'transparent',
                color:       active ? '#3B82F6' : '#94A3B8',
              }}
            >
              {tab.label}
              {count > 0 && (
                <span
                  className="text-xs px-1.5 py-0.5 rounded-full text-white"
                  style={{ background: active ? '#3B82F6' : '#94A3B8' }}
                >
                  {count}
                </span>
              )}
            </button>
          )
        })}
      </div>

      <div className="flex items-center gap-3">
        <div className="relative">
          <button
            onClick={() => setShowTypeDropdown(!showTypeDropdown)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 text-sm text-slate-600 bg-white hover:bg-slate-50"
          >
            {TYPE_OPTIONS.find((o) => o.value === typeFilter)?.label ?? '전체'}
            <ChevronDown size={14} />
          </button>
          {showTypeDropdown && (
            <div className="absolute left-0 top-11 w-36 bg-white rounded-xl border border-slate-200 shadow-lg z-10 overflow-hidden">
              {TYPE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => { setTypeFilter(opt.value); setShowTypeDropdown(false) }}
                  className="w-full text-left px-4 py-2.5 text-sm text-slate-600 hover:bg-slate-50 transition-colors"
                  style={{
                    fontWeight: typeFilter === opt.value ? 600 : 400,
                    color:      typeFilter === opt.value ? '#3B82F6' : undefined,
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        </div>
        <span className="text-xs text-slate-400">{totalCount}건</span>
      </div>

      <div
        className="bg-white rounded-2xl border border-slate-200 overflow-hidden"
        style={{ boxShadow: '0 4px 20px rgba(0,0,0,0.06)' }}
      >
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-100">
              {['신청자', '유형', '기간', '사유', '상태', '신청일', '작업'].map((h) => (
                <th key={h} className="text-left px-5 py-4 text-xs font-semibold text-slate-500">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>

            {!showOnlySwap && filteredTimeOff.map((req) => {
              const tc = TYPE_CONFIG[req.type] ?? TYPE_CONFIG.OFF
              const sc = STATUS_CONFIG[req.status] ?? STATUS_CONFIG.pending
              const elapsed = formatDistanceToNow(new Date(req.created_at), { addSuffix: true, locale: ko })
              return (
                <tr
                  key={`to-${req.request_id}`}
                  className="border-b border-slate-50 hover:bg-slate-50 transition-colors cursor-pointer"
                  onClick={() => openDetail(req)}
                >
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-2.5">
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0"
                        style={{ background: '#3B82F6' }}
                      >
                        {req.requester_name?.charAt(0) ?? '?'}
                      </div>
                      <span className="text-sm font-medium text-slate-700">{req.requester_name}</span>
                    </div>
                  </td>
                  <td className="px-5 py-4">
                    <span className="text-xs font-medium px-2.5 py-1 rounded-full" style={{ background: tc.bg, color: tc.text }}>
                      {tc.label}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-sm text-slate-600">
                    {formatDateRange(req.start_date, req.end_date)}
                  </td>
                  <td className="px-5 py-4 text-sm text-slate-500 max-w-[140px]">
                    <div className="truncate">{req.reason || '-'}</div>
                  </td>
                  <td className="px-5 py-4">
                    <span className="text-xs font-medium px-2.5 py-1 rounded-full" style={{ background: sc.bg, color: sc.text }}>
                      {sc.label}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-xs text-slate-400">{elapsed}</td>
                  <td className="px-5 py-4">
                    {req.status === 'pending' ? (
                      <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => openDetail(req)}
                          className="px-3 py-1.5 rounded-lg text-xs font-medium text-white"
                          style={{ background: '#3B82F6' }}
                        >
                          처리
                        </button>
                      </div>
                    ) : (
                      <span className="text-xs text-slate-300">-</span>
                    )}
                  </td>
                </tr>
              )
            })}

            {(typeFilter === '' || typeFilter === 'SWAP') && filteredSwap.map((req) => {
              const sc = STATUS_CONFIG[req.status] ?? STATUS_CONFIG.pending
              const elapsed = req.created_at
                ? formatDistanceToNow(new Date(req.created_at), { addSuffix: true, locale: ko })
                : '-'
              const isAccepted = req.status === 'accepted'
              const isActive   = req.status === 'pending' || isAccepted
              return (
                <tr
                  key={`sw-${req.swap_request_id}`}
                  className="border-b border-slate-50 hover:bg-slate-50 transition-colors"
                >
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-2.5">
                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center text-white shrink-0"
                        style={{ background: '#8B5CF6' }}
                      >
                        <RefreshCw size={14} />
                      </div>
                      <div>
                        <span className="text-sm font-medium text-slate-700">{req.requester_name}</span>
                        {isAccepted && req.proposer_name && (
                          <div className="text-xs text-slate-400 mt-0.5">
                            {req.requester_name} {req.shift_code} ↕ {req.proposer_name} {req.proposer_shift_code}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-4">
                    <span className="text-xs font-medium px-2.5 py-1 rounded-full" style={{ background: '#EFF6FF', color: '#3B82F6' }}>
                      교대
                    </span>
                  </td>
                  <td className="px-5 py-4 text-sm text-slate-600">
                    {req.work_date ?? '-'}
                  </td>
                  <td className="px-5 py-4 text-sm text-slate-500 max-w-[140px]">
                    <div className="truncate">{req.reason || '-'}</div>
                  </td>
                  <td className="px-5 py-4">
                    <span className="text-xs font-medium px-2.5 py-1 rounded-full" style={{ background: sc.bg, color: sc.text }}>
                      {sc.label}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-xs text-slate-400">{elapsed}</td>
                  <td className="px-5 py-4">
                    {isActive ? (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => isAccepted && setSwapApproveTarget(req)}
                          disabled={!isAccepted}
                          className="px-3 py-1.5 rounded-lg text-xs font-medium text-white transition-opacity"
                          style={{
                            background: '#3B82F6',
                            opacity: isAccepted ? 1 : 0.35,
                            cursor: isAccepted ? 'pointer' : 'not-allowed',
                          }}
                        >
                          승인
                        </button>
                        <button
                          onClick={() => { setSwapRejectTarget(req); setSwapRejectReason('') }}
                          className="px-3 py-1.5 rounded-lg text-xs font-medium text-white"
                          style={{ background: '#EF4444' }}
                        >
                          반려
                        </button>
                      </div>
                    ) : (
                      <span className="text-xs text-slate-300">-</span>
                    )}
                  </td>
                </tr>
              )
            })}

            {filteredTimeOff.length === 0 && filteredSwap.length === 0 && (
              <tr>
                <td colSpan={7} className="text-center py-12 text-sm text-slate-400">
                  {activeStatus
                    ? `${STATUS_CONFIG[activeStatus]?.label} 상태의 요청이 없습니다`
                    : '요청 내역이 없습니다'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
