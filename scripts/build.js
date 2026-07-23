const fs = require('fs');
const path = require('path');

const projectRoot = path.resolve(__dirname, '..');
const buildDir = path.join(projectRoot, 'build');
const legacyPublishDir = path.join(projectRoot, 'npm build');
const staticDir = path.join(projectRoot, 'static');

const htmlPages = [
  'index.html',
  'dashboard.html',
  'chat.html',
  'failures.html',
  'performance.html',
  'trends.html',
  'weekend.html',
  'login.html',
  'logout.html',
  'signin.html',
  'reset_password.html',
];

const routeAliases = [
  'dashboard',
  'chat',
  'failures',
  'performance',
  'trends',
  'weekend',
  'login',
  'logout',
  'signin',
  'reset_password',
];

fs.rmSync(buildDir, { recursive: true, force: true });
fs.rmSync(legacyPublishDir, { recursive: true, force: true });
fs.mkdirSync(buildDir, { recursive: true });

for (const page of htmlPages) {
  const sourcePath = path.join(projectRoot, page);
  if (!fs.existsSync(sourcePath)) {
    continue;
  }
  fs.copyFileSync(sourcePath, path.join(buildDir, page));
}

for (const alias of routeAliases) {
  const sourcePath = path.join(projectRoot, `${alias}.html`);
  if (!fs.existsSync(sourcePath)) {
    continue;
  }
  const aliasDir = path.join(buildDir, alias);
  fs.mkdirSync(aliasDir, { recursive: true });
  fs.copyFileSync(sourcePath, path.join(aliasDir, 'index.html'));
}

if (fs.existsSync(staticDir)) {
  fs.cpSync(staticDir, path.join(buildDir, 'static'), { recursive: true });
}

fs.cpSync(buildDir, legacyPublishDir, { recursive: true });

console.log(`Build complete: ${buildDir}`);