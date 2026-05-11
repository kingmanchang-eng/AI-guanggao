'use client'
import { useState, useEffect } from 'react'
import { api } from '@/lib/api'

type Website = { id: string; domain: string; name: string }
type AdGroup = {
  name: string
  cpc_bid_usd: number
  keywords: { text: string; match_type: string }[]
  negative_keywords: { text: string; match_type: string }[]
  headlines: string[]
  descriptions: string[]
}
type Plan = {
  campaign_name: string
  daily_budget_usd: number
  bidding_strategy: string
  ad_groups: AdGroup[]
}

type Step = 'form' | 'previewing' | 'preview' | 'creating' | 'done'

export default function CampaignsPage() {
  const [websites, setWebsites] = useState<Website[]>([])
  const [websiteId, setWebsiteId] = useState('')
  const [url, setUrl] = useState('')
  const [campaignName, setCampaignName] = useState('')
  const [budget, setBudget] = useState('50')
  const [biddingStrategy, setBiddingStrategy] = useState('MANUAL_CPC')
  const [startPaused, setStartPaused] = useState(true)

  const [step, setStep] = useState<Step>('form')
  const [plan, setPlan] = useState<Plan | null>(null)
  const [pageInfo, setPageInfo] = useState<{ title: string; meta_description: string; headings: string[] } | null>(null)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.listWebsites().then(setWebsites).catch(() => {})
  }, [])

  async function handlePreview() {
    if (!websiteId || !url) { setError('请选择网站并填写落地页 URL'); return }
    setError('')
    setStep('previewing')
    try {
      const res = await api.previewCampaign({
        website_id: websiteId,
        landing_page_url: url,
        campaign_name: campaignName || undefined,
        daily_budget_usd: parseFloat(budget) || 50,
        bidding_strategy: biddingStrategy,
        start_paused: startPaused,
      })
      if (res.error) { setError(res.error); setStep('form'); return }
      setPlan(res.plan)
      setPageInfo(res.page_content)
      setStep('preview')
    } catch (e: any) {
      setError(e.message || '请求失败')
      setStep('form')
    }
  }

  async function handleCreate() {
    setError('')
    setStep('creating')
    try {
      const res = await api.createCampaign({
        website_id: websiteId,
        landing_page_url: url,
        campaign_name: plan?.campaign_name || campaignName || undefined,
        daily_budget_usd: plan?.daily_budget_usd || parseFloat(budget) || 50,
        bidding_strategy: plan?.bidding_strategy || biddingStrategy,
        start_paused: startPaused,
      })
      if (res.error) { setError(res.error); setStep('preview'); return }
      setResult(res)
      setStep('done')
    } catch (e: any) {
      setError(e.message || '创建失败')
      setStep('preview')
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">从落地页创建广告系列</h1>
        <p className="text-sm text-gray-500 mt-1">输入落地页 URL，AI 自动分析内容并生成完整广告结构</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">{error}</div>
      )}

      {/* Step 1: 表单 */}
      {(step === 'form' || step === 'previewing') && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <h2 className="font-semibold text-gray-800">第一步：填写基本信息</h2>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">绑定网站 *</label>
              <select
                value={websiteId}
                onChange={e => setWebsiteId(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">请选择网站</option>
                {websites.map(w => (
                  <option key={w.id} value={w.id}>{w.domain} ({w.name})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">落地页 URL *</label>
              <input
                type="url"
                value={url}
                onChange={e => setUrl(e.target.value)}
                placeholder="https://example.com/product"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">广告系列名称（可选，AI 会自动生成）</label>
              <input
                type="text"
                value={campaignName}
                onChange={e => setCampaignName(e.target.value)}
                placeholder="留空由 AI 生成"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">每日预算（USD）</label>
              <input
                type="number"
                value={budget}
                onChange={e => setBudget(e.target.value)}
                min="1"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">出价策略</label>
              <select
                value={biddingStrategy}
                onChange={e => setBiddingStrategy(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="MANUAL_CPC">手动 CPC</option>
                <option value="MAXIMIZE_CONVERSIONS">最大化转化</option>
                <option value="TARGET_CPA">目标 CPA</option>
              </select>
            </div>
            <div className="flex items-center gap-2 pt-6">
              <input
                type="checkbox"
                id="paused"
                checked={startPaused}
                onChange={e => setStartPaused(e.target.checked)}
                className="rounded"
              />
              <label htmlFor="paused" className="text-sm text-gray-700">创建后暂停（建议勾选，手动审核后再启用）</label>
            </div>
          </div>

          <button
            onClick={handlePreview}
            disabled={step === 'previewing'}
            className="mt-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition-colors"
          >
            {step === 'previewing' ? '⏳ AI 正在分析落地页并生成方案...' : '生成广告方案预览'}
          </button>
        </div>
      )}

      {/* Step 2: 预览 */}
      {(step === 'preview' || step === 'creating') && plan && (
        <>
          {pageInfo && (
            <div className="bg-gray-50 rounded-xl border border-gray-200 p-4 text-sm">
              <p className="font-medium text-gray-700 mb-1">落地页解析结果</p>
              <p className="text-gray-600"><span className="font-medium">标题：</span>{pageInfo.title}</p>
              {pageInfo.meta_description && (
                <p className="text-gray-600 mt-0.5"><span className="font-medium">描述：</span>{pageInfo.meta_description}</p>
              )}
              {pageInfo.headings.length > 0 && (
                <p className="text-gray-600 mt-0.5"><span className="font-medium">页面标题：</span>{pageInfo.headings.slice(0, 4).join(' / ')}</p>
              )}
            </div>
          )}

          <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-semibold text-gray-800">AI 生成的广告方案</h2>
                <p className="text-xs text-gray-500 mt-0.5">确认无误后点击「立即创建」</p>
              </div>
              <button onClick={() => setStep('form')} className="text-sm text-gray-500 hover:text-gray-700">← 重新填写</button>
            </div>

            {/* 广告系列概要 */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: '广告系列名称', value: plan.campaign_name },
                { label: '每日预算', value: `$${plan.daily_budget_usd} USD` },
                { label: '出价策略', value: plan.bidding_strategy },
              ].map(item => (
                <div key={item.label} className="bg-blue-50 rounded-lg p-3">
                  <p className="text-xs text-blue-600 font-medium">{item.label}</p>
                  <p className="text-sm text-gray-800 mt-0.5 font-semibold">{item.value}</p>
                </div>
              ))}
            </div>

            {/* 广告组列表 */}
            <div className="space-y-4">
              {plan.ad_groups.map((ag, i) => (
                <div key={i} className="border border-gray-200 rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium text-gray-800 text-sm">广告组 {i + 1}：{ag.name}</h3>
                    <span className="text-xs text-gray-500">CPC 出价：${ag.cpc_bid_usd}</span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <p className="font-medium text-gray-600 mb-1">关键词（{ag.keywords.length}个）</p>
                      <div className="flex flex-wrap gap-1">
                        {ag.keywords.map((kw, j) => (
                          <span key={j} className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                            {kw.text} <span className="text-gray-400">[{kw.match_type}]</span>
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="font-medium text-gray-600 mb-1">否定关键词（{ag.negative_keywords.length}个）</p>
                      <div className="flex flex-wrap gap-1">
                        {ag.negative_keywords.map((kw, j) => (
                          <span key={j} className="bg-red-50 text-red-600 px-2 py-0.5 rounded">
                            -{kw.text}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="text-xs">
                    <p className="font-medium text-gray-600 mb-1">广告标题（{ag.headlines.length}个）</p>
                    <div className="flex flex-wrap gap-1">
                      {ag.headlines.map((h, j) => (
                        <span key={j} className="bg-green-50 text-green-700 px-2 py-0.5 rounded">{h}</span>
                      ))}
                    </div>
                  </div>

                  <div className="text-xs">
                    <p className="font-medium text-gray-600 mb-1">广告描述（{ag.descriptions.length}个）</p>
                    <div className="space-y-1">
                      {ag.descriptions.map((d, j) => (
                        <p key={j} className="text-gray-600 bg-gray-50 px-2 py-1 rounded">{d}</p>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex gap-3 pt-2">
              <button
                onClick={handleCreate}
                disabled={step === 'creating'}
                className="bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white px-6 py-2.5 rounded-lg text-sm font-medium transition-colors"
              >
                {step === 'creating' ? '⏳ 正在 Google Ads 创建中...' : '立即创建广告系列'}
              </button>
              <button
                onClick={() => setStep('form')}
                disabled={step === 'creating'}
                className="border border-gray-300 text-gray-600 hover:bg-gray-50 px-6 py-2.5 rounded-lg text-sm font-medium transition-colors"
              >
                重新配置
              </button>
            </div>
          </div>
        </>
      )}

      {/* Step 3: 创建结果 */}
      {step === 'done' && result && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
          <div className="flex items-center gap-3">
            <span className="text-2xl">{result.status === 'completed' ? '✅' : '⚠️'}</span>
            <div>
              <h2 className="font-semibold text-gray-800">
                {result.status === 'completed' ? '广告系列创建成功' : '部分创建成功'}
              </h2>
              <p className="text-sm text-gray-500">Plan ID: {result.plan_id}</p>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-3">
            {[
              { label: '广告系列', value: '1' },
              { label: '广告组', value: result.result.ad_groups?.length ?? 0 },
              { label: '关键词', value: result.result.keywords_created ?? 0 },
              { label: '广告', value: result.result.ads_created ?? 0 },
            ].map(item => (
              <div key={item.label} className="bg-gray-50 rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-blue-600">{item.value}</p>
                <p className="text-xs text-gray-500 mt-0.5">{item.label}</p>
              </div>
            ))}
          </div>

          {result.result.campaign_resource && (
            <div className="text-xs text-gray-500 bg-gray-50 rounded p-2 font-mono break-all">
              {result.result.campaign_resource}
            </div>
          )}

          {result.result.errors?.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-sm font-medium text-yellow-800 mb-1">部分步骤出现错误：</p>
              {result.result.errors.map((e: string, i: number) => (
                <p key={i} className="text-xs text-yellow-700">{e}</p>
              ))}
            </div>
          )}

          {startPaused && (
            <p className="text-sm text-gray-500">
              广告系列已创建为<strong>暂停状态</strong>，请在 Google Ads 后台确认无误后手动启用。
            </p>
          )}

          <button
            onClick={() => { setStep('form'); setPlan(null); setResult(null); setUrl(''); setCampaignName('') }}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg text-sm font-medium"
          >
            创建另一个广告系列
          </button>
        </div>
      )}
    </div>
  )
}
