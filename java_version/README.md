# Java TDLib Telegram Group Fetcher

Java implementation using TDLib for fetching Telegram group messages.

## Prerequisites

1. **Java 11+** installed
2. **TDLib native libraries** compiled and available
3. **Gradle** for building

## TDLib Setup

### Windows:
1. Download TDLib precompiled binaries or compile from source
2. Place `tdjni.dll` in your system PATH or project directory
3. Ensure OpenSSL and zlib DLLs are available

### Linux/macOS:
1. Compile TDLib with JNI support:
   ```bash
   git clone https://github.com/tdlib/td.git
   cd td
   mkdir build
   cd build
   cmake -DCMAKE_BUILD_TYPE=Release -DTD_ENABLE_JNI=ON ..
   cmake --build . --target install
   ```

## Configuration

Update credentials in `TelegramGroupFetcher.java`:
```java
private static final int API_ID = your_api_id;
private static final String API_HASH = "your_api_hash";
private static final String PHONE_NUMBER = "+your_phone_number";
```

## Build and Run

```bash
# Build
gradle build

# Run
gradle run
```

## Comparison with Python Version

### Advantages:
- Official TDLib support
- Better performance for large-scale operations
- More robust error handling
- Type safety

### Disadvantages:
- Complex setup (native libraries)
- More boilerplate code
- Platform-specific builds required
- Harder to deploy

## Note

This implementation requires TDLib native libraries to be properly installed and configured on your system.