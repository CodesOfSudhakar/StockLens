import axios from 'axios'
import { credentialHeaders } from '../store/settings.js'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

// Inject Angel One / Groq credentials from localStorage on every call.
api.interceptors.request.use((config) => {
  config.headers = { ...config.headers, ...credentialHeaders() }
  return config
})

export const getOverview = () => api.get('/market/overview').then((r) => r.data)

export const getAnalysis = (symbol, timeframe) =>
  api
    .get('/analysis', { params: { symbol, timeframe } })
    .then((r) => r.data)

export const getNews = (symbol) =>
  api.get('/analysis/news', { params: { symbol } }).then((r) => r.data)

export const runOutlook = (symbol) =>
  api.post('/outlook/run', { symbol }).then((r) => r.data)

export default api
