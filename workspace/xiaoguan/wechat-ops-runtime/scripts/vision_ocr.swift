#!/usr/bin/env swift

import AppKit
import Foundation
import Vision

struct OCRLine: Encodable {
    let text: String
    let confidence: Float
    let boundingBox: [Double]
}

struct OCRResult: Encodable {
    let ok: Bool
    let imagePath: String
    let fullText: String
    let lines: [OCRLine]
}

enum OCRFailure: Error {
    case usage
    case imageLoadFailed(String)
}

func loadImage(_ path: String) throws -> CGImage {
    let url = URL(fileURLWithPath: path)
    guard let image = NSImage(contentsOf: url) else {
        throw OCRFailure.imageLoadFailed(path)
    }
    var proposedRect = CGRect(origin: .zero, size: image.size)
    guard let cgImage = image.cgImage(forProposedRect: &proposedRect, context: nil, hints: nil) else {
        throw OCRFailure.imageLoadFailed(path)
    }
    return cgImage
}

func main() throws {
    guard CommandLine.arguments.count >= 2 else {
        throw OCRFailure.usage
    }

    let imagePath = CommandLine.arguments[1]
    let cgImage = try loadImage(imagePath)
    var recognized: [OCRLine] = []

    let request = VNRecognizeTextRequest { request, error in
        if let error = error {
            fputs("OCR error: \\(error)\\n", stderr)
            return
        }

        guard let observations = request.results as? [VNRecognizedTextObservation] else {
            return
        }

        for observation in observations {
            guard let candidate = observation.topCandidates(1).first else { continue }
            let box = observation.boundingBox
            recognized.append(
                OCRLine(
                    text: candidate.string,
                    confidence: candidate.confidence,
                    boundingBox: [
                        Double(box.origin.x),
                        Double(box.origin.y),
                        Double(box.size.width),
                        Double(box.size.height),
                    ]
                )
            )
        }
    }

    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    request.recognitionLanguages = ["zh-Hans", "en-US"]

    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    try handler.perform([request])

    let fullText = recognized.map { $0.text }.joined(separator: "\\n")
    let result = OCRResult(ok: true, imagePath: imagePath, fullText: fullText, lines: recognized)
    let encoder = JSONEncoder()
    encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
    let data = try encoder.encode(result)
    FileHandle.standardOutput.write(data)
}

do {
    try main()
} catch OCRFailure.usage {
    fputs("Usage: vision_ocr.swift /path/to/image.png\\n", stderr)
    exit(2)
} catch OCRFailure.imageLoadFailed(let path) {
    fputs("Failed to load image: \(path)\n", stderr)
    exit(1)
} catch {
    fputs("Unexpected OCR failure: \(error)\n", stderr)
    exit(1)
}
