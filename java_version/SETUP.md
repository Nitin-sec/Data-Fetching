# Java TDLib Telegram Group Fetcher Setup

## Prerequisites

1. **Java 11+** installed
2. **Visual Studio 2019/2022** with C++ build tools
3. **CMake** (https://cmake.org/download/)
4. **Git**
5. **vcpkg** for dependencies

## Step 1: Install vcpkg

```bash
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat
.\vcpkg install openssl:x64-windows zlib:x64-windows gperf:x64-windows
```

## Step 2: Build TDLib

```bash
git clone https://github.com/tdlib/td.git
cd td
mkdir jnibuild
cd jnibuild

cmake -DCMAKE_BUILD_TYPE=Release ^
      -DTD_ENABLE_JNI=ON ^
      -A x64 ^
      -DCMAKE_TOOLCHAIN_FILE=C:\path\to\vcpkg\scripts\buildsystems\vcpkg.cmake ^
      -DJAVA_HOME="C:\Program Files\Java\jdk-11" ^
      -DCMAKE_INSTALL_PREFIX=..\example\java\td ^
      ..

cmake --build . --target install --config Release
```

## Step 3: Copy Required Files

Copy these files to the java_version directory:
- `td.jar` (from TDLib build)
- `tdjni.dll` (from TDLib build)
- `libssl-1_1-x64.dll` (from vcpkg)
- `libcrypto-1_1-x64.dll` (from vcpkg)
- `zlib1.dll` (from vcpkg)

## Step 4: Update Credentials

Edit `data_fetcher_test.java`:
```java
private static final int API_ID = your_actual_api_id;
private static final String API_HASH = "your_actual_api_hash";
private static final String PHONE_NUMBER = "+your_phone_number";
```

## Step 5: Compile and Run

```bash
javac -cp "td.jar" data_fetcher_test.java
java -cp ".;td.jar" -Djava.library.path=. org.telegram.fetcher.data_fetcher_test
```

## Alternative: Use Gradle

```bash
gradle build
gradle run
```

## Note

This setup is complex. Consider using the Python version with Telethon for easier setup and deployment.