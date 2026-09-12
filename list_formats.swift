import AVFoundation
import CoreMedia

let session = AVCaptureDevice.DiscoverySession(
   deviceTypes: [.external],
   mediaType: .video, position: .unspecified)
for d in session.devices {
   print("DEVICE \(d.localizedName) [\(d.uniqueID)]")
   for f in d.formats {
       let dim = CMVideoFormatDescriptionGetDimensions(f.formatDescription)
       let sub = CMFormatDescriptionGetMediaSubType(f.formatDescription)
       let cc = String(format: "%c%c%c%c",
                       (sub >> 24) & 255, (sub >> 16) & 255,
                       (sub >> 8) & 255, sub & 255)
       let rates = f.videoSupportedFrameRateRanges
           .map { String(format: "%.1f-%.1f", $0.minFrameRate, $0.maxFrameRate) }
           .joined(separator: ",")
       print("  \(dim.width)x\(dim.height)  \(cc)  fps=\(rates)")
   }
}

