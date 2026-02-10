Execute Sprint 4: Build the React Dashboard.

PREREQUISITE: Sprint 3 must be complete (API returning real data at localhost:8000).

Goal: Working web interface that Gujarat Police officers can use.

## TASK 1: Initialize React Project (10 min)

```bash
cd src/dashboard
npm create vite@latest . -- --template react-ts
npm install
npm install tailwindcss @tailwindcss/vite
npm install react-router-dom axios @tanstack/react-query
npm install lucide-react recharts
npm install -D @types/react @types/react-dom
```

Set up Tailwind in vite.config.ts.
Create src/lib/api.ts with axios instance pointing to http://localhost:8000.
Set up React Query provider in main.tsx.

## TASK 2: Auth & Layout (20 min)

- Login page with Gujarat Police branding (dark blue #1B3A5C)
- JWT token storage in memory (NOT localStorage for security)
- Axios interceptor for auto-attaching token and auto-refresh
- Protected route wrapper
- Main layout with sidebar navigation

## TASK 3: Core Pages (60 min)

Build these pages connecting to real API endpoints:

1. **Dashboard Home** (`/`) - Stats cards + quick actions
2. **SOP Assistant** (`/sop`) - Form → API call → display results with citations
3. **Chargesheet Review** (`/chargesheet`) - Upload/paste → API call → display score + issues
4. **Case Search** (`/search`) - Search bar + filters → results list
5. **Section Converter** (`/tools/sections`) - Input section → show equivalent

## TASK 4: Polish (20 min)

- Loading spinners on all API calls
- Error messages (user-friendly, not raw errors)
- Responsive layout (test at mobile width)
- Empty states ("No results found")

## TASK 5: Test

```bash
cd src/dashboard
npm run dev
```

Open http://localhost:5173, login, test each page.

## DONE CRITERIA:
- Can login and navigate all pages
- SOP page returns investigation guidance
- Search page returns results
- Section converter works
- Print "SPRINT 4 COMPLETE - DASHBOARD WORKING"
