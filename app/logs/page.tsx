'use client'
import { useState } from 'react'
import useSWR from 'swr'
import { api } from '@/lib/api'

const RISK_COLOR: Record<string, string> = {
  low: 'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-red-100 text-red-700',
}

const STATUS_COLOR: Record<string, string> = {
  pending: 'bg-gray-100 text-gray-600',
  executed: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
  rejected: 'bg-orange-100 text-orange-700',
}

export default function LogsPage() {
  const [websiteId, setWebsiteId] = useState('')
  const [tab, setTab] = useState<'actions' | 'mutate'>('actions')
  const { data: websites } = useSWR('websites', api.listWebsites)
  const { data: actions } = useSWR(
    websiteId ? `actions-${websiteId}` : null,
    () => api.listActions(websiteId)
  )
  const { data: mutateLogs } = useSWR(
    websiteId && tab === 'mutate' ? `logs-${websiteId}` : null,
    () => api.listMutateLogs(websiteId)
  )

  return (
    <div className="p-8">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">操作日志</h2>
        <p className="text-sm text-gray-500 mt-1">查看 AI 决策动作和 Google Ads API 执行结果</p>
      </div>

      <div className="flex items-center gap-4 mb-6">
        <select
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white"
          value={websiteId}
          onChange={e => setWebsiteId(e.target.value)}
        >
          <option value="">选择网站...</option>
          {websites?.map((w: any) => (
            <option key={w.id} value={w.id}>{w.domain}</option>
          ))}
        </select>

        <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
          {[['actions', 'AI 动作'], ['mutate', 'API 执行日志']].map(([k, label]) => (
            <button key={k} onClick={() => setTab(k as any)}
              className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                tab === k ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-600'
              }`}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {!websiteId && (
        <div className="bg-white rounded-xl p-12 text-center text-gray-400 shadow-sm border border-gray-100">
          请先选择一个网站查看日志
        </div>
      )}

      {websiteId && tab === 'actions' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="font-semibold text-gray-900">AI 动作记录（{actions?.length ?? 0}）</h3>
          </div>
          <div className="divide-y divide-gray-50">
            {!actions && <p className="px-6 py-8 text-center text-gray-400 text-sm">加载中...</p>}
            {actions?.length === 0 && <p className="px-6 py-8 text-center text-gray-400 text-sm">暂无记录</p>}
            {actions?.map((a: any) => (
              <div key={a.id} className="px-6 py-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-sm font-medium text-gray-900">{a.action_type}</span>
                      {a.risk_level && (
                        <span className={`px-2 py-0.5 text-xs rounded-full ${RISK_COLOR[a.risk_level] ?? 'bg-gray-100 text-gray-600'}`}>
                          {a.risk_level}
                        </span>
                      )}
                      <span className={`px-2 py-0.5 text-xs rounded-full ${STATUS_COLOR[a.status] ?? 'bg-gray-100 text-gray-600'}`}>
                        {a.status}
                      </span>
                      {a.confidence && (
                        <span className="text-xs text-gray-400">置信度 {Math.round(a.confidence * 100)}%</span>
                      )}
                    </div>
                    {a.reason && (
                      <p className="text-sm text-gray-500 mt-1 truncate">{a.reason}</p>
                    )}
                    <p className="text-xs text-gray-400 mt-1">
                      {a.campaign_id && `campaign: ${a.campaign_id}`}
                      {a.ad_group_id && ` · ad_group: ${a.ad_group_id}`}
                    </p>
                  </div>
                  <p className="text-xs text-gray-400 whitespace-nowrap">
                    {new Date(a.created_at).toLocaleString('zh-CN')}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {websiteId && tab === 'mutate' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="font-semibold text-gray-900">API 执行日志（{mutateLogs?.length ?? 0}）</h3>
          </div>
          <div className="divide-y divide-gray-50">
            {!mutateLogs && <p className="px-6 py-8 text-center text-gray-400 text-sm">加载中...</p>}
            {mutateLogs?.length === 0 && <p className="px-6 py-8 text-center text-gray-400 text-sm">暂无执行记录</p>}
            {mutateLogs?.map((l: any) => (
              <div key={l.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${l.success ? 'bg-green-500' : 'bg-red-500'}`} />
                    <span className="text-sm font-medium text-gray-900">
                      {l.success ? '执行成功' : '执行失败'}
                    </span>
                    {l.validate_only && (
                      <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">仅验证</span>
                    )}
                  </div>
                  <p className="text-xs text-gray-400">{new Date(l.created_at).toLocaleString('zh-CN')}</p>
                </div>
                {l.error_message && (
                  <p className="text-sm text-red-600 mt-1 font-mono text-xs">{l.error_message}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
