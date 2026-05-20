import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8012',
  timeout: 180000
})

export function getToken() {
  return localStorage.getItem('medical_agent_token') || ''
}

export function setAuth(token, user) {
  localStorage.setItem('medical_agent_token', token)
  localStorage.setItem('medical_agent_user', JSON.stringify(user || {}))
}

export function clearAuth() {
  localStorage.removeItem('medical_agent_token')
  localStorage.removeItem('medical_agent_user')
}

export function getStoredUser() {
  try { return JSON.parse(localStorage.getItem('medical_agent_user') || 'null') } catch { return null }
}

api.interceptors.request.use(config => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export async function login(phone, password) {
  const { data } = await api.post('/api/auth/login', { phone, password })
  setAuth(data.token, data.user)
  return data
}

export async function register(phone, password, displayName = '', idNumber = '') {
  const { data } = await api.post('/api/auth/register', {
    phone,
    password,
    display_name: displayName,
    id_number: idNumber
  })
  setAuth(data.token, data.user)
  return data
}

export async function getMe() {
  const { data } = await api.get('/api/auth/me')
  return data.user
}

export async function updateMe(payload) {
  const { data } = await api.patch('/api/auth/me', payload)
  setAuth(getToken(), data.user)
  return data.user
}

export async function getSessions(scene = '') {
  const { data } = await api.get('/api/sessions', { params: scene ? { scene } : {} })
  return data.sessions
}

export async function getSessionMessages(sessionId) {
  const { data } = await api.get(`/api/sessions/${sessionId}/messages`)
  return data.messages || []
}

export async function deleteSession(sessionId) {
  const { data } = await api.delete(`/api/sessions/${sessionId}`)
  return data
}

export async function getMetrics() {
  const { data } = await api.get('/api/metrics')
  return data
}

export async function getRecords(days = 7) {
  const { data } = await api.get('/api/records', { params: { days } })
  return data.records
}

export async function getReports() {
  const { data } = await api.get('/api/reports')
  return data.reports
}

export async function interpretReport(reportId) {
  const { data } = await api.get(`/api/reports/${reportId}/interpret`)
  return data
}

export async function getMedicalDocuments() {
  const { data } = await api.get('/api/upload/medical-documents')
  return data.documents || []
}

export async function getMedicalDocument(docId) {
  const { data } = await api.get(`/api/upload/medical-document/${docId}`)
  return data
}

export function rawDocUrl(docId) {
  return `${api.defaults.baseURL}/api/upload/medical-document/${docId}/raw?access_token=${encodeURIComponent(getToken())}`
}

export async function getDepartments() {
  const { data } = await api.get('/api/departments')
  return data.departments
}

export async function getSchedule(department) {
  const { data } = await api.get('/api/appointments/schedule', { params: { department } })
  return data
}

export async function createAppointment(payload) {
  const { data } = await api.post('/api/appointments', payload)
  return data
}

export async function getAppointments() {
  const { data } = await api.get('/api/appointments')
  return data.appointments
}

export async function cancelAppointment(appointmentId) {
  const { data } = await api.delete(`/api/appointments/${appointmentId}`)
  return data
}

export async function getSettings() {
  const { data } = await api.get('/api/settings')
  return data
}

export async function clearAllData() {
  const { data } = await api.delete('/api/sessions')
  return data
}

export async function deleteMyReports() {
  const { data } = await api.delete('/api/upload/admin/my-reports')
  return data
}

export async function deleteAllReports() {
  const { data } = await api.delete('/api/upload/admin/all-reports')
  return data
}

// ========== 多模态附件 ==========
export async function uploadMedicalDocument(file, { sessionId = null, docTypeHint = null, note = null, onProgress } = {}) {
  const form = new FormData()
  form.append('file', file)
  if (sessionId) form.append('session_id', sessionId)
  if (docTypeHint) form.append('doc_type_hint', docTypeHint)
  if (note) form.append('note', note)
  const { data } = await api.post('/api/upload/medical-document', form, {
    timeout: 300000,
    onUploadProgress: onProgress
  })
  return data
}

// ========== 流式对话 ==========
/**
 * @param {string} scene - triage | consultation | medication
 * @param {object} payload - ChatRequest payload
 * @param {object} handlers - { onSession, onTrace, onEvidence, onChunk, onDone, onError }
 * @returns { promise, abort }
 */
export function streamMedicalChat(scene, payload, handlers = {}) {
  const sceneMap = {
    triage: '/api/triage/stream',
    consultation: '/api/consultation/stream',
    medication: '/api/medication/stream'
  }
  const url = `${api.defaults.baseURL}${sceneMap[scene]}`
  const ctrl = new AbortController()
  const promise = (async () => {
    let resp
    try {
      resp = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {})
        },
        body: JSON.stringify(payload),
        signal: ctrl.signal
      })
    } catch (err) {
      handlers.onError && handlers.onError(err)
      throw err
    }
    if (!resp.ok || !resp.body) {
      const detail = await resp.text().catch(() => '')
      const err = new Error(`HTTP ${resp.status}: ${detail || resp.statusText}`)
      handlers.onError && handlers.onError(err)
      throw err
    }
    const reader = resp.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      let idx
      while ((idx = buffer.indexOf('\n\n')) !== -1) {
        const raw = buffer.slice(0, idx).trim()
        buffer = buffer.slice(idx + 2)
        if (!raw.startsWith('data:')) continue
        const data = raw.slice(5).trim()
        if (data === '[DONE]') return
        let evt
        try { evt = JSON.parse(data) } catch { continue }
        switch (evt.type) {
          case 'session': handlers.onSession && handlers.onSession(evt); break
          case 'trace': handlers.onTrace && handlers.onTrace(evt); break
          case 'evidence': handlers.onEvidence && handlers.onEvidence(evt); break
          case 'chunk': handlers.onChunk && handlers.onChunk(evt.delta || ''); break
          case 'done': handlers.onDone && handlers.onDone(evt); break
          case 'error': handlers.onError && handlers.onError(new Error(evt.detail || 'stream error')); break
        }
      }
    }
  })()
  return { promise, abort: () => ctrl.abort() }
}

// 多文件并发上传
export async function uploadMedicalDocumentsConcurrent(files, { sessionId = null, onProgress, onItemDone } = {}) {
  const results = []
  let completed = 0
  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    try {
      const result = await uploadMedicalDocument(file, {
        sessionId,
        onProgress: (evt) => {
          if (onProgress) onProgress(i, evt)
        }
      })
      results.push({ ok: true, data: result })
      if (onItemDone) onItemDone(i, { ok: true, data: result })
    } catch (err) {
      results.push({ ok: false, error: err.message || '上传失败' })
      if (onItemDone) onItemDone(i, { ok: false, error: err.message || '上传失败' })
    }
    completed++
  }
  return results
}

// ========== 新功能API（增强版）==========

// 健康数据记录（增强版）
export async function createHealthRecord(payload) {
  const { data } = await api.post('/api/health-records', payload)
  return data
}

export async function getHealthRecords(params = {}) {
  const { data } = await api.get('/api/health-records', { params })
  return data.records
}

export async function getHealthTrends(recordType, days = 30) {
  const { data } = await api.get('/api/health-records/trends', { params: { record_type: recordType, days } })
  return data
}

export async function deleteHealthRecord(recordId) {
  const { data } = await api.delete(`/api/health-records/${recordId}`)
  return data
}

// 健康统计
export async function getHealthStats() {
  const { data } = await api.get('/api/health-stats')
  return data
}

// 家庭成员管理（增强版）
export async function createFamilyMember(payload) {
  const { data } = await api.post('/api/family-members', payload)
  return data
}

export async function getFamilyMembers() {
  const { data } = await api.get('/api/family-members')
  return data.members
}

export async function updateFamilyMember(memberId, payload) {
  const { data } = await api.put(`/api/family-members/${memberId}`, payload)
  return data
}

export async function deleteFamilyMember(memberId) {
  const { data } = await api.delete(`/api/family-members/${memberId}`)
  return data
}

// 健康打卡（增强版）
export async function createCheckin(payload) {
  const { data } = await api.post('/api/checkins', payload)
  return data
}

export async function getCheckins(params = {}) {
  const { data } = await api.get('/api/checkins', { params })
  return data.checkins
}

export async function deleteCheckin(checkinId) {
  const { data } = await api.delete(`/api/checkins/${checkinId}`)
  return data
}

// 打卡任务/习惯
export async function createCheckinTask(payload) {
  const { data } = await api.post('/api/checkin-tasks', payload)
  return data
}

export async function getCheckinTasks(activeOnly = true) {
  const { data } = await api.get('/api/checkin-tasks', { params: { active_only: activeOnly } })
  return data.tasks
}

export async function deleteCheckinTask(taskId) {
  const { data } = await api.delete(`/api/checkin-tasks/${taskId}`)
  return data
}

// 收藏（增强版）
export async function createFavorite(payload) {
  const { data } = await api.post('/api/favorites', payload)
  return data
}

export async function getFavorites(params = {}) {
  const { data } = await api.get('/api/favorites', { params })
  return data.favorites
}

export async function deleteFavorite(favoriteId) {
  const { data } = await api.delete(`/api/favorites/${favoriteId}`)
  return data
}

// 消息通知（增强版）
export async function getNotifications(params = {}) {
  const { data } = await api.get('/api/notifications', { params })
  return data
}

export async function markNotificationRead(notifId) {
  const { data } = await api.post(`/api/notifications/${notifId}/read`)
  return data
}

export async function markAllNotificationsRead() {
  const { data } = await api.post('/api/notifications/read-all')
  return data
}

export async function deleteNotification(notifId) {
  const { data } = await api.delete(`/api/notifications/${notifId}`)
  return data
}

// 健康目标
export async function createHealthGoal(payload) {
  const { data } = await api.post('/api/health-goals', payload)
  return data
}

export async function getHealthGoals(activeOnly = true) {
  const { data } = await api.get('/api/health-goals', { params: { active_only: activeOnly } })
  return data.goals
}

export async function updateHealthGoalProgress(goalId, currentValue) {
  const { data } = await api.put(`/api/health-goals/${goalId}/progress`, null, { params: { current_value: currentValue } })
  return data
}

// 健康洞察
export async function getHealthInsights(unreadOnly = false) {
  const { data } = await api.get('/api/health-insights', { params: { unread_only: unreadOnly } })
  return data.insights
}

export async function markInsightRead(insightId) {
  const { data } = await api.post(`/api/health-insights/${insightId}/read`)
  return data
}

// 健康工具（增强版）
export async function calculateBMI(height, weight, saveToRecords = false) {
  const { data } = await api.get('/api/tools/bmi', { params: { height, weight, save_to_records: saveToRecords } })
  return data
}

export async function evaluateBloodPressure(systolic, diastolic, saveToRecords = false) {
  const { data } = await api.get('/api/tools/blood-pressure', { params: { systolic, diastolic, save_to_records: saveToRecords } })
  return data
}

export async function evaluateBloodSugar(value, saveToRecords = false) {
  const { data } = await api.get('/api/tools/blood-sugar', { params: { value, save_to_records: saveToRecords } })
  return data
}

export async function evaluateBloodGlucose(value, timeOfDay = '空腹', saveToRecords = false) {
  const { data } = await api.get('/api/tools/blood-glucose', { params: { value, time_of_day: timeOfDay, save_to_records: saveToRecords } })
  return data
}
