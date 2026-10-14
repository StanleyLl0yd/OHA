// SPDX-License-Identifier: MPL-2.0
using System.Runtime.InteropServices;

namespace OHA.Windows;

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
