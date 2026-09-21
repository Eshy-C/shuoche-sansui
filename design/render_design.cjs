const fs = require('node:fs/promises');
const path = require('node:path');
const sharp = require('sharp');

const directory = path.join(__dirname, '说车三岁-界面设计');
const screens = [
  ['01-车辆录入首页.svg', '车辆录入首页'],
  ['02-车辆照片九宫格.svg', '车辆照片九宫格'],
  ['03-卖点与视频偏好.svg', '卖点与视频偏好'],
];

async function main() {
  const composites = [];
  const labels = [];
  for (const [index, [filename, title]] of screens.entries()) {
    const source = await fs.readFile(path.join(directory, filename));
    const screenshot = await sharp(source, { density: 216 }).png().toBuffer();
    if (index === 0) {
      await fs.writeFile(path.join(directory, '说车三岁-首页效果图.png'), screenshot);
    }
    const left = 80 + index * 445;
    const scaled = await sharp(screenshot).resize(780, 1688).png().toBuffer();
    composites.push({ input: scaled, left: left * 2, top: 196 * 2 });
    labels.push(`<text x="${left}" y="177" font-size="11" fill="#958BA5">0${index + 1}</text><text x="${left + 26}" y="177" font-size="14" font-weight="500" fill="#363144">${title}</text><rect x="${left - 1}" y="195" width="392" height="846" rx="3" fill="#FFFFFF"/>`);
  }

  const board = `<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="1120" viewBox="0 0 1440 1120">
  <rect width="1440" height="1120" fill="#EFEDF5"/>
  <g font-family="PingFang SC, Hiragino Sans GB, Microsoft YaHei, sans-serif">
    <text x="80" y="43" font-size="10" letter-spacing="2.6" fill="#8A7F9D">SHUOCHE SANSUI / MINI PROGRAM</text>
    <text x="80" y="93" font-size="36" font-weight="600" fill="#202235">说车三岁</text>
    <text x="243" y="91" font-size="31" font-weight="300" fill="#A097AF">/</text>
    <text x="273" y="91" font-size="30" font-weight="500" fill="#4E455D">车辆录入</text>
    <text x="80" y="122" font-size="14" fill="#81778D">先收集完整素材，再把好车介绍清楚。</text>
    <rect x="1099" y="74" width="116" height="29" rx="14.5" fill="none" stroke="#D6D0E2"/>
    <text x="1157" y="93" font-size="11" fill="#81738F" text-anchor="middle">390 × 844</text>
    <rect x="1227" y="74" width="133" height="29" rx="14.5" fill="none" stroke="#D6D0E2"/>
    <text x="1293.5" y="93" font-size="11" fill="#81738F" text-anchor="middle">3 个可编辑 SVG</text>
    ${labels.join('')}
    <text x="80" y="1082" font-size="11" fill="#91879E">销售形象 → 车辆九宫格 → 卖点与视频偏好</text>
    <text x="1360" y="1082" font-size="11" fill="#91879E" text-anchor="end">文字保留 · 分组清晰 · 按钮独立命名</text>
  </g></svg>`;

  await sharp(Buffer.from(board), { density: 144 })
    .composite(composites)
    .png()
    .toFile(path.join(directory, '说车三岁-三页总览.png'));

  for (const filename of ['说车三岁-首页效果图.png', '说车三岁-三页总览.png']) {
    const metadata = await sharp(path.join(directory, filename)).metadata();
    console.log(`${filename}: ${metadata.width} × ${metadata.height}`);
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
