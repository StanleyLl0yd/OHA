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

[StructLayout(LayoutKind.Sequential)]
internal struct AnalysisV1
{
    public uint StructSize;
    public uint Version;
    public ulong InputBytes;
    public ulong SampledBytes;
    public double EntropyBitsPerByte;
    public double AsciiRatio;
    public double ZeroRatio;
    public uint UniqueByteValues;
    public uint ContentHint;
    public ulong Reserved0;
    public ulong Reserved1;
}

internal static class Native
{
    [DllImport("oha_ffi", EntryPoint = "oha_api_version", CallingConvention = CallingConvention.Cdecl)]
    internal static extern uint OhaApiVersion();

    [DllImport("oha_ffi", EntryPoint = "oha_analyze_bytes_v1", CallingConvention = CallingConvention.Cdecl)]
    internal static extern int OhaAnalyzeBytes([In] byte[] input, ulong length, ref AnalysisV1 output);
}
