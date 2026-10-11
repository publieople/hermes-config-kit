/// Full SCManager service enumeration pattern.
/// Requires cargo feature: "Win32_System_Services"

use windows::{
    core::HSTRING,
    Win32::System::Services::{
        CloseServiceHandle, EnumServicesStatusW, OpenSCManagerW, OpenServiceW,
        QueryServiceConfigW, SC_MANAGER_ENUMERATE_SERVICE, SERVICE_AUTO_START,
        SERVICE_STATE_ALL, SERVICE_WIN32,
    },
};

fn enumerate_auto_services() -> Vec<(String, String)> {
    let mut out = Vec::new();
    let scm = unsafe { OpenSCManagerW(None, None, SC_MANAGER_ENUMERATE_SERVICE) };
    let scm = match scm {
        Ok(h) => h,
        Err(e) => { eprintln!("OpenSCManagerW: {e:?}"); return out; }
    };

    // First call — get buffer size.
    let mut buf_size = 0u32;
    let mut count = 0u32;
    unsafe {
        let _ = EnumServicesStatusW(scm, SERVICE_WIN32, SERVICE_STATE_ALL,
            None, 0, &mut buf_size, &mut count, None);
    }
    if count == 0 { unsafe { _ = CloseServiceHandle(scm); }; return out; }

    // Second call — actual data.
    let mut buf: Vec<u8> = vec![0u8; buf_size as usize];
    unsafe {
        if EnumServicesStatusW(scm, SERVICE_WIN32, SERVICE_STATE_ALL,
            Some(buf.as_mut_ptr() as *mut _), buf_size, &mut buf_size, &mut count, None
        ).is_err() {
            _ = CloseServiceHandle(scm); return out;
        }
    }

    let entry_size = std::mem::size_of::<
        windows::Win32::System::Services::ENUM_SERVICE_STATUSW>();
    for i in 0..count as usize {
        let ptr = buf.as_ptr();
        let entry = unsafe {
            &*(ptr.add(i * entry_size) as *const windows::Win32::System::Services::ENUM_SERVICE_STATUSW)
        };
        let svc_display = unsafe { entry.lpDisplayName.to_string().unwrap_or_default() };

        let svc = match unsafe { OpenServiceW(scm, &HSTRING::from(
            &unsafe { entry.lpServiceName.to_string().unwrap_or_default() }
        ), SERVICE_QUERY_CONFIG | SERVICE_QUERY_STATUS) } {
            Ok(h) => h, Err(_) => continue,
        };

        let mut bytes_needed = 0u32;
        if unsafe { QueryServiceConfigW(svc, None, 0, &mut bytes_needed) }.is_ok() || bytes_needed == 0 {
            unsafe { _ = CloseServiceHandle(svc); }; continue;
        }

        let config_buf = vec![0u8; bytes_needed as usize];
        let mut ret = bytes_needed;
        let ok = unsafe {
            QueryServiceConfigW(svc,
                Some(config_buf.as_ptr() as *mut windows::Win32::System::Services::QUERY_SERVICE_CONFIGW),
                config_buf.len() as u32, &mut ret)
        };
        if ok.is_ok() {
            let config = unsafe { &*(config_buf.as_ptr()
                as *const windows::Win32::System::Services::QUERY_SERVICE_CONFIGW) };
            if config.dwStartType == SERVICE_AUTO_START {
                let cmd = unsafe { config.lpBinaryPathName.to_string().unwrap_or_default() };
                out.push((svc_display, cmd));
            }
        }
        unsafe { _ = CloseServiceHandle(svc); };
    }
    unsafe { _ = CloseServiceHandle(scm); };
    out
}
