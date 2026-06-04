const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();

  await page.emulateMediaType('print');

  const filePath = path.resolve(__dirname, '../docs/presentation.html');
  await page.goto('file://' + filePath, { waitUntil: 'networkidle0' });

  await page.pdf({
    path: path.resolve(__dirname, '../docs/presentation.pdf'),
    format: 'A4',
    landscape: true,
    printBackground: true,
    margin: { top: 0, right: 0, bottom: 0, left: 0 },
  });

  await browser.close();
  console.log('PDF exported to docs/presentation.pdf');
})();
