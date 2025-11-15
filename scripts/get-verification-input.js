// Script to extract Standard JSON Input for verification
const fs = require('fs');
const path = require('path');

// Find the build info file
const buildInfoDir = path.join(__dirname, '..', 'artifacts', 'build-info');
const files = fs.readdirSync(buildInfoDir);
const buildInfoFile = path.join(buildInfoDir, files[0]);

console.log('Reading build info from:', buildInfoFile);

const buildInfo = JSON.parse(fs.readFileSync(buildInfoFile, 'utf8'));

// Extract Standard JSON Input
const standardJsonInput = buildInfo.input;

// Save to file
const outputFile = path.join(__dirname, '..', 'standard-json-input.json');
fs.writeFileSync(outputFile, JSON.stringify(standardJsonInput, null, 2));

console.log('\n✅ Standard JSON Input saved to:', outputFile);
console.log('\n📋 Contract Name: DePINToken');
console.log('\n📋 Constructor Arguments:');
console.log('  "Moxi AI"');
console.log('  "MOXI"');
console.log('  1000000000000000000000000000');
console.log('  1000000000');
console.log('  1000000000000000000000');
console.log('  604800');

