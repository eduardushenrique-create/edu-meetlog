const { spawn } = require('child_process');
const path = require('path');

exports.default = async function afterPack(context) {
  const { appOutDir, platform } = context;
  
  if (platform.name === 'windows') {
    const exePath = path.join(appOutDir, 'Edu MeetLog.exe');
    console.log('Build completed:', exePath);
  }
};