const puppeteer = require('puppeteer');
const path = require('path');
const { pathToFileURL } = require('url');

(async () => {
  let browser;
  try {
    browser = await puppeteer.launch({
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });

    const page = await browser.newPage();
    await page.emulateMediaType('print');

    const filePath = path.resolve(__dirname, '../docs/presentation.html');
    await page.goto(pathToFileURL(filePath).toString(), { waitUntil: 'networkidle0' });

    await page.pdf({
      path: path.resolve(__dirname, '../docs/presentation.pdf'),
      format: 'A4',
      landscape: true,
      printBackground: true,
      margin: { top: 0, right: 0, bottom: 0, left: 0 },
    });

    console.log('PDF exported to docs/presentation.pdf');
  } catch (error) {
    console.error('Erro ao exportar o PDF:', error);
    process.exitCode = 1;
  } finally {
    if (browser) await browser.close();
  }
})();
