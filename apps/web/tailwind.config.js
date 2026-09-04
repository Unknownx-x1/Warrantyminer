/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: {
          bg: '#f4f6f9',        // Crisp modern light gray canvas
          surface: '#ffffff',   // Pure white primary surfaces
          subtle: '#f8fafc',    // Elevated card header / secondary surface
          muted: '#f1f5f9',     // Inset panels / telemetry blocks
          border: '#e2e8f0',    // Clean subtle dividers
          borderStrong: '#cbd5e1',
        },
        ink: {
          primary: '#0f172a',   // Slate-900 high-contrast primary text
          secondary: '#334155', // Slate-700 body copy
          muted: '#64748b',     // Slate-500 metadata
          faint: '#94a3b8',     // Slate-400 placeholder & subtle notes
        },
        brand: {
          primary: '#2563eb',   // Royal Blue accent
          hover: '#1d4ed8',
          subtle: '#eff6ff',
          border: '#bfdbfe',
        },
        status: {
          critical: '#dc2626',
          criticalBg: '#fef2f2',
          criticalBorder: '#fecaca',
          warning: '#d97706',
          warningBg: '#fffbeb',
          warningBorder: '#fde68a',
          success: '#059669',
          successBg: '#ecfdf5',
          successBorder: '#a7f3d0',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace']
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.04)',
        'elevated': '0 4px 6px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -2px rgba(0, 0, 0, 0.04)',
        'modal': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.06)',
      }
    },
  },
  plugins: [],
}
