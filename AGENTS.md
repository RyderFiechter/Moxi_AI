# Repository Guidelines

## Project Structure & Module Organization
Smart-contract sources live in `contracts/` (e.g., `DePINToken.sol`) and emit build products under `artifacts/`, `cache/`, and `typechain-types/`. Deployment and ownership scripts sit in `scripts/`, while reproducible deployments are stored in `deployments/`. Tests reside in `test/` and follow the `*.test.ts` suffix. The storage node prototype is in `node/` (Python) and the Next.js control dapp is under `dapp/`; keep their dependency trees isolated to avoid inflating the root lockfile. Docs such as `README.md`, `QUICKSTART.md`, and `DEPLOYMENT.md` describe flows—touch them whenever you add a feature or network.

## Build, Test, and Development Commands
- `npm run compile`: Hardhat compile plus TypeChain generation after contract changes.
- `npm run node`: Starts the local Hardhat JSON-RPC node on `localhost:8545`.
- `npm run deploy:local|arbitrum|optimism|base`: Runs `scripts/deploy.ts` with the network preset.
- `npm run test`: Executes the Mocha/Chai suite via Hardhat.
- `npx hardhat coverage`: Writes Solidity coverage artifacts for CI review.
- `npx hardhat run scripts/verify.ts --network <network>`: Verifies bytecode; ensure `.env` exposes the explorer API key.

## Coding Style & Naming Conventions
Solidity files use 4-space indentation, `pragma ^0.8.20`, and PascalCase contract names (`DePINToken`). Functions/events stay `camelCase`, storage vars descriptive, and enums/errors `PascalCase`. TypeScript helpers use 2-space indentation, ES modules, and filenames that match the contract under test (e.g., `DePINToken.test.ts`). Run Prettier (`npx prettier --write "contracts/**/*.sol" "scripts/**/*.ts" "test/**/*.ts"`) before review to keep ABI/computed hashes stable. Store `PRIVATE_KEY`, `RPC_URL`, and explorer tokens in `.env` and never commit the file.

## Testing Guidelines
Add assertions under `test/*.test.ts` using Hardhat fixtures; mirror the behavior name inside each `describe("stake")` block so failures map to features. Reset state via `loadFixture` for determinism, and focus on staking windows, pausing, reward math, and role checks whenever those areas change. Run `npm test` and `npx hardhat coverage` before review, attaching reproduction notes if infrastructure (RPC, explorer keys) is missing.

## Commit & Pull Request Guidelines
Commits follow the current history: one imperative sentence with a trailing period (e.g., `Add staking reward regression tests.`). Bundle related contract, script, and doc edits so deployments remain auditable. Each PR must state motivation, list verification steps (`npm run compile`, `npm test`, deployments), and link issue IDs. Add screenshots or CLI captures when modifying `dapp/` or `node/`. Confirm the relevant `deployments/` JSON matches the code prior to merge.
