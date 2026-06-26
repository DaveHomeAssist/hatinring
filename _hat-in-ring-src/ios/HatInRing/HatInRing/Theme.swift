import SwiftUI

enum HIRTheme {
    static let parchment = Color(hex: 0xE7E1D2)
    static let paper = Color(hex: 0xFBF8F0)
    static let paperAlt = Color(hex: 0xF4EFE2)
    static let navy = Color(hex: 0x13294B)
    static let navyDeep = Color(hex: 0x0E2342)
    static let accentRed = Color(hex: 0x9E3B34)
    static let liveRed = Color(hex: 0xCE2029)
    static let border = Color(hex: 0xE2D9C3)
    static let borderStrong = Color(hex: 0xD8CFB8)
    static let mutedText = Color(hex: 0x7A7460)
    static let softText = Color(hex: 0x857E69)
    static let chipFill = Color(hex: 0xEFE8D6)
    static let segmentFill = Color(hex: 0xEAE1CB)

    static func display(_ size: CGFloat, weight: Font.Weight = .semibold) -> Font {
        .system(size: size, weight: weight, design: .serif)
    }

    static func body(_ size: CGFloat, weight: Font.Weight = .regular) -> Font {
        .system(size: size, weight: weight, design: .default)
    }

    static func mono(_ size: CGFloat, weight: Font.Weight = .regular) -> Font {
        .system(size: size, weight: weight, design: .monospaced)
    }

    static func statusColor(_ tier: Int) -> Color {
        switch tier {
        case 5: return Color(hex: 0x9E3B34)
        case 4: return Color(hex: 0xB26A1C)
        case 3: return Color(hex: 0xA8842C)
        case 2: return Color(hex: 0x3F5C86)
        case 1: return Color(hex: 0x7C8794)
        default: return Color(hex: 0xA7ABA6)
        }
    }

    static func confidenceColor(_ confidence: String) -> Color {
        switch confidence {
        case "Very high": return Color(hex: 0x2E7D4F)
        case "High": return Color(hex: 0x3A8F55)
        case "Medium": return Color(hex: 0xA8842C)
        case "Low": return Color(hex: 0xB08A2A)
        default: return Color(hex: 0xB0AEA4)
        }
    }

    static func partyColor(_ party: String) -> Color {
        switch party {
        case "Democrat": return Color(hex: 0x3F5C86)
        case "Republican": return Color(hex: 0x9E3B34)
        case "Libertarian": return Color(hex: 0xA8842C)
        case "Independent": return Color(hex: 0x3E7E72)
        default: return Color(hex: 0x7A7A7A)
        }
    }
}

extension Color {
    init(hex: UInt32) {
        let red = Double((hex >> 16) & 0xFF) / 255.0
        let green = Double((hex >> 8) & 0xFF) / 255.0
        let blue = Double(hex & 0xFF) / 255.0
        self.init(red: red, green: green, blue: blue)
    }
}
