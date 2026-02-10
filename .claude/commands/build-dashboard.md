Build the Gujarat Police Investigation Support Dashboard frontend.

Tech: React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui
Must be: responsive (mobile-friendly for field officers), fast, works on slow 3G connections.

## Setup
Initialize in `src/dashboard/`:
```bash
cd src/dashboard
pnpm create vite . --template react-ts
pnpm add tailwindcss @tailwindcss/vite shadcn-ui lucide-react axios react-router-dom @tanstack/react-query recharts
```

## Pages:

### 1. Login Page (`/login`)
- Clean, professional, Gujarat Police branding
- Primary color: dark blue (#1B3A5C), white background
- JWT auth with remember-me
- Gujarati + English labels

### 2. Dashboard Home (`/`)
- Quick stats cards: cases reviewed, suggestions used, pending reviews
- Recent activity feed
- Quick action buttons: "New FIR Review", "Check Chargesheet", "Search Cases"

### 3. SOP Assistant (`/sop`)
- Step 1: Select case category (dropdown: theft, murder, assault, robbery, cheating, dowry, NDPS, kidnapping, etc.)
- Step 2: Enter/paste FIR details OR upload FIR document
- Step 3: Click "Get Investigation Guidance"
- Output: Ordered checklist with priority (critical/important/recommended), source references, timeline, common mistakes
- "Export as PDF" button

### 4. Chargesheet Review (`/chargesheet`)
- Upload chargesheet (PDF/DOC/text)
- Show: completeness score 0-100%, missing elements (red), weak points (yellow), good elements (green)
- Side panel: similar successful chargesheets
- "Generate Report" button

### 5. Case Search (`/search`)
- Search bar with natural language input
- Filters: date range, district, category, sections, outcome
- Results with relevance score and preview
- "Find Similar Cases" on each result

### 6. Pattern Insights (`/analytics`)
- Crime hotspot heat map (pilot districts)
- Trend charts (crime category over time) using recharts
- Conviction rate by category/district
- Common chargesheet deficiencies chart

### 7. Section Converter (`/tools/sections`)
- Input: section number + source code (IPC/BNS/CrPC/BNSS)
- Output: equivalent in other code with description
- Useful quick-reference tool for officers

### 8. Training (`/training`)
- Module cards (clickable)
- Quiz exercises
- Progress tracking
- Certificate on completion

## Design Requirements:
- Every label in English AND Gujarati
- Big, clear buttons (officers may not be tech-savvy)
- Loading states for all API calls
- Error boundaries with user-friendly messages
- Dark mode support
- PWA manifest for mobile installation

## API Integration:
- Use axios with JWT interceptor (auto-refresh tokens)
- React Query for data fetching with caching
- API base URL from environment variable

Build with Vite, include Dockerfile for Nginx serving.
