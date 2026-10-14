// SPDX-License-Identifier: MPL-2.0
using System;
using System.Runtime.InteropServices;
using System.Text;
using OHA.Windows;

if (Marshal.SizeOf<AnalysisV1>() != 72 || Native.OhaApiVersion() != 1)
{
    throw new InvalidOperationException("OHA native ABI/layout mismatch");
}

byte[] bytes = Encoding.UTF8.GetBytes("OHA Windows C# to Rust FFI probe\n");
var result = new AnalysisV1
{
    StructSize = (uint)Marshal.SizeOf<AnalysisV1>(),
    Version = 1
};
int code = Native.OhaAnalyzeBytes(bytes, (ulong)bytes.Length, ref result);
if (code != 0 || result.SampledBytes != (ulong)bytes.Length || result.ContentHint != 1)
{
    throw new InvalidOperationException($"Unexpected OHA Rust result {code}, {result.SampledBytes}, {result.ContentHint}");
}

result.Version = 2;
if (Native.OhaAnalyzeBytes(bytes, (ulong)bytes.Length, ref result) != 4)
{
    throw new InvalidOperationException("Invalid ABI layout was not rejected");
}

Console.WriteLine("OHA Windows C# -> Rust FFI PASS");
