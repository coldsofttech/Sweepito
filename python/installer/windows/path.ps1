# Adds a folder to, or removes it from, the PATH of the user or the machine. Run by the CLI
# installer and its uninstaller (installer/windows/nsis/common.nsh).
#
# NSIS strings are limited to 1024 characters, which would cut a long PATH, so the registry is edited
# here. The value type is kept (PATH is normally REG_EXPAND_SZ) and %VARIABLES% are not expanded.
param(
    [Parameter(Mandatory)][ValidateSet('Add', 'Remove')][string]$Action,
    [Parameter(Mandatory)][ValidateSet('User', 'Machine')][string]$Scope,
    [Parameter(Mandatory)][string]$Dir
)

$ErrorActionPreference = 'Stop'

if ($Scope -eq 'Machine') {
    $hive = [Microsoft.Win32.Registry]::LocalMachine
    $subKey = 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
} else {
    $hive = [Microsoft.Win32.Registry]::CurrentUser
    $subKey = 'Environment'
}

$key = $hive.OpenSubKey($subKey, $true)
try {
    $current = [string]$key.GetValue('Path', '', [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
    $kind = [Microsoft.Win32.RegistryValueKind]::ExpandString
    if ($key.GetValueNames() -contains 'Path') { $kind = $key.GetValueKind('Path') }

    $target = $Dir.TrimEnd('\')
    $entries = @($current -split ';' | Where-Object { $_ -ne '' })
    $others = @($entries | Where-Object { $_.TrimEnd('\') -ne $target })

    if ($Action -eq 'Add') {
        # Already there: leave the order alone.
        $updated = if ($others.Count -ne $entries.Count) { $entries } else { $others + $target }
    } else {
        $updated = $others
    }

    $text = $updated -join ';'
    if ($text -ne $current) { $key.SetValue('Path', $text, $kind) }
} finally {
    $key.Close()
}

# Tell running programs (Explorer, new terminals) that the environment changed.
Add-Type -Namespace Win32 -Name Native -MemberDefinition @'
[DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
public static extern IntPtr SendMessageTimeout(IntPtr hWnd, uint Msg, UIntPtr wParam, string lParam,
    uint fuFlags, uint uTimeout, out UIntPtr lpdwResult);
'@
$result = [UIntPtr]::Zero
# HWND_BROADCAST, WM_SETTINGCHANGE, SMTO_ABORTIFHUNG, 5 seconds
[void][Win32.Native]::SendMessageTimeout([IntPtr]0xffff, 0x1A, [UIntPtr]::Zero, 'Environment', 2, 5000, [ref]$result)
