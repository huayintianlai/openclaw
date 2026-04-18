// Photoshop ExtendScript - 打开 PSD 并保存为 PDF
// 这个脚本可以通过 Photoshop 的脚本菜单运行

#target photoshop

// 配置文件路径
var psdPath = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/资本存款_FinalTest_SARL_temp.psd";
var pdfPath = "/Users/xiaojiujiu2/Downloads/资本存款_FinalTest_SARL_PS_ExtendScript.pdf";

try {
    // 打开 PSD 文件
    var psdFile = new File(psdPath);
    if (!psdFile.exists) {
        alert("错误: PSD 文件不存在\n" + psdPath);
    } else {
        var doc = app.open(psdFile);

        // 配置 PDF 保存选项
        var pdfSaveOptions = new PDFSaveOptions();
        pdfSaveOptions.encoding = PDFEncoding.JPEG;
        pdfSaveOptions.jpegQuality = 12; // 最高质量
        pdfSaveOptions.embedColorProfile = true;
        pdfSaveOptions.optimizeForWeb = false;

        // 保存为 PDF
        var pdfFile = new File(pdfPath);
        doc.saveAs(pdfFile, pdfSaveOptions, true, Extension.LOWERCASE);

        // 关闭文档
        doc.close(SaveOptions.DONOTSAVECHANGES);

        alert("✅ PDF 保存成功\n" + pdfPath);
    }
} catch (e) {
    alert("❌ 错误: " + e.message + "\n" + e.line);
}
