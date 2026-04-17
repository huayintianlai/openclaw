#target photoshop

// 从动态替换的占位符读取参数
var psdPath = "PSD_PATH_PLACEHOLDER";
var pdfPath = "PDF_PATH_PLACEHOLDER";
var companyName = "COMPANY_NAME_PLACEHOLDER";
var companyAddress = "COMPANY_ADDRESS_PLACEHOLDER";
var depositDate = "DEPOSIT_DATE_PLACEHOLDER";
var signDate = "SIGN_DATE_PLACEHOLDER";

try {
    // 打开 PSD 文件
    var psdFile = new File(psdPath);
    if (!psdFile.exists) {
        throw new Error("PSD 文件不存在: " + psdPath);
    }

    var doc = app.open(psdFile);
    app.refresh();

    // 定义精确的文本属性配置
    var textConfigs = {
        "公司名称": {
            content: companyName,
            font: "TimesNewRomanPSMT",
            size: 44.0,
            color: {r: 35, g: 35, b: 35},
            fauxBold: true,
            tracking: companyName.length > 15 ? 0 : (companyName.length > 10 ? 30 : 75),  // 根据长度动态调整
            justification: Justification.LEFT
        },
        "公司地址": {
            content: companyAddress,
            font: "TimesNewRomanPSMT",
            size: 47.0,
            color: {r: 25, g: 25, b: 25},
            fauxBold: true,
            tracking: 33
        },
        "资本存款时间": {
            content: depositDate,
            font: "TimesNewRomanPSMT",
            size: 44.0,
            color: {r: 35, g: 35, b: 35},
            fauxBold: true,
            tracking: 45
        },
        "落款时间": {
            content: signDate,
            font: "TimesNewRomanPSMT",
            size: 44.0,
            color: {r: 35, g: 35, b: 35},
            fauxBold: true,
            tracking: 0
        }
    };

    // 遍历所有图层，找到目标文本图层并精确设置属性
    for (var i = 0; i < doc.layers.length; i++) {
        var layer = doc.layers[i];

        if (layer.kind === LayerKind.TEXT) {
            var layerName = layer.name;

            if (textConfigs.hasOwnProperty(layerName)) {
                var config = textConfigs[layerName];
                var textItem = layer.textItem;

                // 设置文本内容
                textItem.contents = config.content;

                // 设置字体
                textItem.font = config.font;

                // 设置字号
                textItem.size = new UnitValue(config.size, "pt");

                // 设置颜色
                var textColor = new SolidColor();
                textColor.rgb.red = config.color.r;
                textColor.rgb.green = config.color.g;
                textColor.rgb.blue = config.color.b;
                textItem.color = textColor;

                // 设置 FauxBold
                textItem.fauxBold = config.fauxBold;

                // 设置 Tracking (字间距)
                textItem.tracking = config.tracking;

                // 确保 BaselineShift 为 0
                textItem.baselineShift = new UnitValue(0, "pt");
            }
        }
    }

    // 拼合图层
    doc.flatten();

    // 调整图像分辨率以控制文件大小
    // 目标：约 1.1M 文件大小
    // 测试结果: 300 DPI = 1.8M, 250 DPI = 1.5M, 230 DPI = 1.3M, 225 DPI = 1.3M
    // 使用 220 DPI 应该产生约 1.1M
    doc.resizeImage(
        UnitValue(1819, "px"),  // 220 DPI 的 A4 宽度
        UnitValue(2574, "px"),  // 220 DPI 的 A4 高度
        220,                     // 分辨率 220 DPI
        ResampleMethod.BICUBIC
    );

    // 配置 PDF 保存选项
    // A4 尺寸 @ 225 DPI，文件大小约 1.1M
    var pdfSaveOptions = new PDFSaveOptions();
    pdfSaveOptions.encoding = PDFEncoding.JPEG;
    pdfSaveOptions.jpegQuality = 11;  // 高质量
    pdfSaveOptions.embedColorProfile = true;
    pdfSaveOptions.optimizeForWeb = false;
    pdfSaveOptions.downgradeColorProfile = false;
    pdfSaveOptions.layers = false;
    pdfSaveOptions.pDFStandard = PDFStandard.NONE;
    pdfSaveOptions.pDFCompatibility = PDFCompatibility.PDF17;

    // 保存为 PDF
    var pdfFile = new File(pdfPath);
    doc.saveAs(pdfFile, pdfSaveOptions, true, Extension.LOWERCASE);

    // 关闭文档
    doc.close(SaveOptions.DONOTSAVECHANGES);

    // 成功标记
    var successFile = new File("/tmp/ps_perfect_export_success.txt");
    successFile.open("w");
    successFile.write(pdfPath);
    successFile.close();

} catch (e) {
    // 错误标记
    var errorFile = new File("/tmp/ps_perfect_export_error.txt");
    errorFile.open("w");
    errorFile.write(e.message + " (Line: " + e.line + ")");
    errorFile.close();
}
