# 🛡️ VaultWares Enterprise-wide Guidelines for Programming Projects

- **What is VaultWares?**
VaultWares is a premium SaaS and e-commerce platform built with a "Privacy-First" philosophy that aims to educate and protect its users. It leverages a modern, type-safe stack to deliver a seamless experience while shopping for high-value digital services and physical goods. It handles a vast array of projects in many different spheres that all have a common goal: data-privacy. It is very important to educate and spread awareness about the impact of data-tracking in our society.

These are general guidelines to apply when coding under the VaultWares umbrella. Use common sense to determine what applies to your project. Prioritize security, performance, and scalability in that order. Always follow best practices for the specific language and framework you are using, but when in doubt, refer to these guidelines.

## 🚀 Core Tech Stack (varies by project, needs, and team preferences)

- **Google Cloud Services Integration:** If possible, use Google Cloud Run, Deploy, Build, SQL Tools, etc.

- **Frontend Frameworks:** Next.js 15+ (App Router), Django, Blazor

- **Languages:** TypeScript (Strict mode), Python, C#

- **Styling:** Tailwind CSS with both light and dark mode support. Refer to STYLE.md for more details.

- **State Management:** TanStack Query (React Query) for server state; Zustand for local state.

- **Database/Backend:** CloudSQL Tools: PostgreSQL, GCP Secret Manager

- **UI Components:** Radix UI primitives / Shadcn UI / VaultWares' own Glass UI library.

- **Validation:** Zod for schema validation, especially for API responses and form inputs or plain old TypeScript validation.

- **Native Apps Frontend:** WinUI 3 for Windows Apps, PyQt or PySide for Python GUI

- **Native Apps Backend:** C# .Net, Python

## 🛠️ Coding Standards & Patterns

- **When generating code for VaultWares projects, adhere to the following when applicable:**

- **Component Architecture:** Use Functional Components with Arrow Syntax. Favor Server Components for data fetching and Client Components only when interactivity is required.

- **Always separate your declarations with a space:** (e.g., x = 5, not x=5)

- **Add empty lines between logical blocks of code for better readability. For example:** Separate imports, component definitions, hooks, and return statements with empty lines.

- **Use consistent indentation:** (4 spaces) and avoid mixing tabs and spaces.

- **Keep comments inside functions to a minimum:** if you need to define behavior, do it when declaring the function, not inside it. When using an external library method, leave a comment indicating the default values and any important considerations.

- **Follow language conventions for anything else.**

## 📛 Naming Conventions: 

- **Components:** PascalCase (e.g., ProductVault.tsx)

- **Hooks:** camelCase starting with 'use' (e.g., useVaultAuth.ts)

- **Utilities:** kebab-case (e.g., format-currency.ts)

## 🏆 Coding Best Practices

- **Type Safety:** Avoid any at all costs. Use Zod for schema validation (especially for API responses and form inputs).

- **Performance:** Keep the bloating to a minimum and optimize your methods. e.g., Implement React Suspense for loading states and utilize Next.js Image component for all assets.

- **CorrelationId:** Always implement the functionality 'CorrelationId' in logs to allow easy debugging. The CorrelationId should be a 7 alphanumeric characters string that starts with a lowercase 'c' (e.g., c1a2b3c). This allows us to easily trace logs related to a specific request or action across the entire system.

- **Code Review:** Review your code before finalizing to make sure there are no syntax errors, trailing artifacts, debugging statements, unused imports, etc.

- **API Routes:** Use Next.js API routes for serverless functions. Validate all inputs with Zod and handle errors gracefully.

## 🎨 Style Guide (Tailwind)

**View STYLE.md**

## 🔒 Security Principles

- **Minimalist Footprint:** Zero-dependency policy for non-essential features.

- **Security First:** Follow OWASP Principles. Always sanitize user inputs. If writing SQL or Supabase queries, ensure Row Level Security (RLS) is considered.

- **Error Handling:** Use a centralized error-boundary pattern. Don't just console.log(error); provide user-friendly feedback using a Toast component.

- **DRY (Don't Repeat Yourself):** Look for existing code that can be reused. e.g., check @/components/ui before creating new UI elements to avoid duplicating Shadcn components.

## 🛠️ Getting Started
- **Pull the latest version:** `git fetch; git pull`

## Run Development:

- **For Node.js projects:**
Install dependencies with `npm install`.
Create a `.env.local` with your Supabase keys.
Run `npm run build && npm run start`. 

- **For Python projects:**
Create a local `.venv` and install Python dependencies with `pip install -r requirements.txt`.

Create a `your-project.cmd` next to `your-project.py` with the following content:
```cmd
@echo off
python "%~dp0your-project.py" %*
```
Then add the cmd folder to PATH and run:
```powershell
your-project your-command your-argument --your-flags
```