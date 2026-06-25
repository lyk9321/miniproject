// frontend/src/api/mocks/dashboard.js
export const mockAdminDashboard = {
  total_employees: 7,
  today_working: 5,
  today_on_leave: 1,
  pending_requests: 4,
  this_week_schedule: [
    { date: '2026-05-04', day: '월', count: 5 },
    { date: '2026-05-05', day: '화', count: 4 },
    { date: '2026-05-06', day: '수', count: 3 },
    { date: '2026-05-07', day: '목', count: 5 },
    { date: '2026-05-08', day: '금', count: 4 },
    { date: '2026-05-09', day: '토', count: 2 },
    { date: '2026-05-10', day: '일', count: 1 },
  ],
}

export const mockEmployeeDashboard = {
  today_schedule: {
    work_date: '2026-05-04', shift_code: 'D', shift_label: '주간',
    shift_color: '#3B82F6', start_time: '08:00', end_time: '16:00',
    is_work_day: true,
  },
  this_week: [
    { work_date: '2026-05-04', day_label: '월', shift_code: 'D',   shift_label: '주간', shift_color: '#3B82F6', is_today: true  },
    { work_date: '2026-05-05', day_label: '화', shift_code: 'D',   shift_label: '주간', shift_color: '#3B82F6', is_today: false },
    { work_date: '2026-05-06', day_label: '수', shift_code: null,  shift_label: null,   shift_color: null,      is_today: false },
    { work_date: '2026-05-07', day_label: '목', shift_code: 'E',   shift_label: '오후', shift_color: '#8B5CF6', is_today: false },
    { work_date: '2026-05-08', day_label: '금', shift_code: 'N',   shift_label: '야간', shift_color: '#1D4ED8', is_today: false },
    { work_date: '2026-05-09', day_label: '토', shift_code: 'OFF', shift_label: '휴무', shift_color: '#94A3B8', is_today: false },
    { work_date: '2026-05-10', day_label: '일', shift_code: 'OFF', shift_label: '휴무', shift_color: '#94A3B8', is_today: false },
  ],
  my_requests: [
    { request_id: 1, type: 'OFF',  date_display: '5/10', status: 'pending', created_at: '2026-05-01T10:00:00Z' },
    { request_id: 2, type: 'SWAP', date_display: '5/1',  status: 'pending', created_at: '2026-05-01T09:00:00Z' },
  ],
}
