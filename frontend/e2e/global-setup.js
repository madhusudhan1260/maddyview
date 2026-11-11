import { execFileSync } from 'node:child_process'

// Start every run from an empty account, even when an already-running e2e server is reused.
// Only ever touches the throwaway finpilot_e2e database.
export default function globalSetup() {
  execFileSync('psql', ['-q', '-d', 'finpilot_e2e', '-c', 'TRUNCATE users RESTART IDENTITY CASCADE'], { stdio: 'inherit' })
}
