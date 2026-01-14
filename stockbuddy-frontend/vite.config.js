import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        // 手動分割代碼塊
        manualChunks: {
          // React 核心
          'vendor-react': ['react', 'react-dom'],
          // 圖表相關組件
          'charts': [
            './src/components/CandlestickChart.jsx',
            './src/components/InstitutionalChart.jsx',
            './src/components/AdvancedCharts.jsx',
          ],
          // 分析相關組件
          'analysis': [
            './src/components/PatternRecognition.jsx',
            './src/components/HistoricalPerformance.jsx',
            './src/components/AIReport.jsx',
          ],
          // 交易相關組件
          'trading': [
            './src/components/SimulationTrading.jsx',
            './src/components/TransactionManager.jsx',
            './src/components/PortfolioDashboard.jsx',
          ],
        }
      }
    },
    // 提高 chunk 大小警告閾值
    chunkSizeWarningLimit: 600,
  }
})
