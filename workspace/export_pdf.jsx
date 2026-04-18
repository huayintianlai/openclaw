// Photoshop JSX 脚本 - 打开 PSD 并导出为 PDF
// 用法: 通过命令行调用 Photoshop 执行此脚本

// 从命令行参数获取文件路径
var psdPath = app.scriptArgs.getValue("psd");
var pdfPath = app.scriptArgs.getValue("pdf");

if (!psdPath || !pdfPath) {
    alert("错误: 缺少参数\n用法: -psd <psd文件路径> -pdf <pdf输出路径>");
    app.quit();
}

try {
    // 打开 PSD 文件
    var psdFile = new File(psdPath);
    if (!psdFile.exists) {
        alert("错误: PSD 文件不存在 - " + psdPath);
        app.quit();
    }

    var doc = app.open(psdFile);

    // 设置 PDF 保存选项
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

    // 退出 Photoshop
    app.quit();

} catch (e) {
    alert("错误: " + e.message);
    app.quit();
}
