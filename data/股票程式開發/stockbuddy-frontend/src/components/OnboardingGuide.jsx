/**
 * OnboardingGuide.jsx - 新手引導組件
 * V10.23 新增
 *
 * 功能：
 * - 首次使用時顯示引導教學
 * - 介紹主要功能
 * - 支援跳過和下一步
 * - 使用 localStorage 記錄已看過
 */

import React, { useState, useEffect } from 'react';

const ONBOARDING_KEY = 'stockbuddy_onboarding_completed';

const OnboardingGuide = ({ onComplete }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);

  // 引導步驟
  const steps = [
    {
      title: '歡迎使用 StockBuddy',
      icon: '📈',
      content: '您的專屬台股智能選股助手！我們將幫助您做出更明智的投資決策。',
      highlight: null,
    },
    {
      title: 'AI 精選推薦',
      icon: '🎯',
      content: '我們使用多維度分析（技術面、基本面、籌碼面、新聞面）為您篩選最具潛力的股票。',
      tip: '點擊任一股票卡片可查看詳細分析',
      highlight: 'ai',
    },
    {
      title: '綜合投資策略',
      icon: '📋',
      content: '提供專業投顧級的完整投資策略，包含進出場價位、止損止盈建議、風險評估等。',
      tip: '非常適合想要完整投資計畫的用戶',
      highlight: 'strategy',
    },
    {
      title: '選股篩選器',
      icon: '🔍',
      content: '根據您的偏好設定篩選條件，如本益比、殖利率、ROE 等，找出符合條件的股票。',
      tip: '有多種預設策略可快速套用',
      highlight: 'screener',
    },
    {
      title: '價格警示',
      icon: '🔔',
      content: '設定目標價或止損價，當股價觸及時會收到通知，不再錯過任何機會。',
      tip: '支援瀏覽器推播通知',
      highlight: 'alerts',
    },
    {
      title: '績效追蹤',
      icon: '📊',
      content: '追蹤 AI 推薦的歷史表現，查看勝率和平均報酬率，讓您對系統更有信心。',
      tip: '透明化的績效數據',
      highlight: 'tracker',
    },
    {
      title: '開始使用',
      icon: '🚀',
      content: '一切準備就緒！點擊下方按鈕開始探索 StockBuddy 的強大功能。',
      tip: '有任何問題可以查看說明或聯繫我們',
      highlight: null,
    },
  ];

  // 檢查是否需要顯示引導
  useEffect(() => {
    const completed = localStorage.getItem(ONBOARDING_KEY);
    if (!completed) {
      setIsVisible(true);
    }
  }, []);

  // 下一步
  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  // 上一步
  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  // 完成引導
  const handleComplete = () => {
    localStorage.setItem(ONBOARDING_KEY, 'true');
    setIsVisible(false);
    if (onComplete) onComplete();
  };

  // 跳過引導
  const handleSkip = () => {
    handleComplete();
  };

  // 重置引導（供設定頁使用）
  const resetOnboarding = () => {
    localStorage.removeItem(ONBOARDING_KEY);
    setCurrentStep(0);
    setIsVisible(true);
  };

  if (!isVisible) return null;

  const currentStepData = steps[currentStep];
  const progress = ((currentStep + 1) / steps.length) * 100;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="relative w-full max-w-lg mx-4">
        {/* 卡片 */}
        <div className="bg-slate-800 rounded-2xl border border-slate-700 shadow-2xl overflow-hidden">
          {/* 進度條 */}
          <div className="h-1 bg-slate-700">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>

          {/* 內容 */}
          <div className="p-8">
            {/* 圖標 */}
            <div className="text-6xl text-center mb-6">{currentStepData.icon}</div>

            {/* 標題 */}
            <h2 className="text-2xl font-bold text-white text-center mb-4">
              {currentStepData.title}
            </h2>

            {/* 說明 */}
            <p className="text-slate-300 text-center mb-4 leading-relaxed">
              {currentStepData.content}
            </p>

            {/* 小提示 */}
            {currentStepData.tip && (
              <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3 text-center mb-4">
                <span className="text-blue-400 text-sm">💡 {currentStepData.tip}</span>
              </div>
            )}

            {/* 步驟指示器 */}
            <div className="flex justify-center gap-2 mb-6">
              {steps.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentStep(index)}
                  className={`w-2 h-2 rounded-full transition-all ${
                    index === currentStep
                      ? 'bg-blue-500 w-6'
                      : index < currentStep
                      ? 'bg-blue-500/50'
                      : 'bg-slate-600'
                  }`}
                />
              ))}
            </div>

            {/* 按鈕區 */}
            <div className="flex items-center justify-between">
              <button
                onClick={handleSkip}
                className="text-slate-400 hover:text-white text-sm transition-colors"
              >
                跳過教學
              </button>

              <div className="flex gap-3">
                {currentStep > 0 && (
                  <button
                    onClick={handlePrev}
                    className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                  >
                    上一步
                  </button>
                )}
                <button
                  onClick={handleNext}
                  className="px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white rounded-lg font-medium transition-all"
                >
                  {currentStep === steps.length - 1 ? '開始使用' : '下一步'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* 關閉按鈕 */}
        <button
          onClick={handleSkip}
          className="absolute -top-2 -right-2 w-8 h-8 bg-slate-700 hover:bg-slate-600 rounded-full flex items-center justify-center text-slate-400 hover:text-white transition-colors"
        >
          ✕
        </button>
      </div>
    </div>
  );
};

// 重新觀看引導按鈕組件
export const ReplayOnboardingButton = () => {
  const handleReplay = () => {
    localStorage.removeItem(ONBOARDING_KEY);
    window.location.reload();
  };

  return (
    <button
      onClick={handleReplay}
      className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-sm transition-colors"
    >
      <span>📖</span>
      <span>重新觀看教學</span>
    </button>
  );
};

export default OnboardingGuide;
