using System;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.UI.Xaml;

namespace OHA.Windows;

public sealed partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
    }

    private void ProbeButton_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            if (Native.OhaApiVersion() != 1)
            {
                ProbeResult.Text = "Incompatible Rust ABI";
                return;
            }
            var data = Encoding.UTF8.GetBytes("OHA local Rust probe\n");
            var result = new AnalysisV1
            {
                StructSize = (uint)Marshal.SizeOf<AnalysisV1>(),
                Version = 1
            };
            var status = Native.OhaAnalyzeBytes(data, (ulong)data.Length, ref result);
            ProbeResult.Text = status == 0
                ? $"Rust analyzed {result.SampledBytes} bytes, entropy {result.EntropyBitsPerByte:F2} bits/byte"
                : $"Rust returned status {status}";
        }
        catch (DllNotFoundException)
        {
            ProbeResult.Text = "Rust native library is missing. Place oha_ffi.dll alongside the application executable.";
        }
        catch (EntryPointNotFoundException)
        {
            ProbeResult.Text = "Rust ABI symbols not found.";
        }
        catch (BadImageFormatException)
        {
            ProbeResult.Text = "Incorrect Rust library architecture. Use Windows x64.";
        }
    }
}
