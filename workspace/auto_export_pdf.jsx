// Photoshop ExtendScript - 从命令行参数读取路径
#target photoshop

// 从环境变量或参数读取路径
var psdPath = app.getenv("PSD_PATH");
var pdfPath = app.getenv("PDF_PATH");

if (!psdPath || !pdfPath) {
    // 如果环境变量不存在，使用默认路径（用于测试）
    psdPath = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/资本存款_FinalTest_SARL_temp.psd";
    pdfPath = "/Users/xiaojiujiu2/Downloads/资本存款_FinalTest_SARL_PS_Auto.pdf";
}

try {
    // 打开 PSD 文件
    var psdFile = new File(psdPath);
    if (!psdFile.exists) {
        throw new Error("PSD 文件不存在: " + psdPath);
    }

    var doc = app.open(psdFile);

    // 配置 PDF 保存选项
    var pdfSaveOptions = new PDFSaveOptions();
    pdfSaveOptions.encoding = PDFEncoding.JPEG;
    pdfSaveOptions.jpegQuality = 12; // 最高质量
    pdfSaveOptions.embedColorProfile = true;
    pdfSaveOptions.optimizeForWeb = false;
    pdfSaveOptions.downgradeColorProfile = false;

    // 保存为 PDF
    var pdfFile = new File(pdfPath);
    doc.saveAs(pdfFile, pdfSaveOptions, true, Extension.LOWERCASE);

    // 关闭文档
    doc.close(SaveOptions.DONOTSAVECHANGES);

    // 成功标记
    var successFile = new File("/tmp/ps_export_success.txt");
    successFile.open("w");
    successFile.write(pdfPath);
    successFile.close();

} catch (e) {
    // 错误标记
    var errorFile = new File("/tmp/ps_export_error.txt");
    errorFile.open("w");
    errorFile.write(e.message);
    errorFile.close();
}

// 退出 Photoshop
app.quit();
