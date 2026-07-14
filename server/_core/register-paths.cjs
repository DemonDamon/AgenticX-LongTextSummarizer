// Register tsconfig paths at runtime for Node.js path alias resolution
const path = require('path');
const { register } = require('tsconfig-paths');

// Use __dirname to construct absolute path to tsconfig.json
const tsconfigPath = path.resolve(__dirname, '../../tsconfig.json');
const tsconfig = require(tsconfigPath);

register({
  baseUrl: tsconfig.compilerOptions.baseUrl || '.',
  paths: tsconfig.compilerOptions.paths || {},
});
