"""Authored foundation cases, with falsifiable mental-model probes.

Correct choices stay server-side; display order is randomized per learner.
These are foundation checkpoints, not claims of full subject mastery.
"""
CASES = {}

def case(n, lesson, artifact, task, answers, model, evidence, transfer):
    CASES[n] = dict(lesson=lesson.split('\n\n'), artifact=artifact, task=task,
                    answers=answers.split('|'), probes=[
        dict(key='model', title='Causal model', question='Which explanation accounts for the result?', options=model.split('|')),
        dict(key='evidence', title='Evidence', question='Which observation best tests that explanation?', options=evidence.split('|')),
        dict(key='transfer', title='Counterfactual', question=transfer[0], options=transfer[1].split('|')),
    ])

case(42,
'''Isolation is a property of the entire experiment, not the name of a network. A bridged VM can share a route with real equipment. Authorization specifies the assets, permitted actions, time window, and stop conditions; access alone is not permission.

Separate simulated processes from physical actuators. Snapshot test systems, use synthetic samples, and verify the absence of external routes before experiments. Electrical work needs appropriate equipment and training; a software stop button is not an electrical isolation device. ESD protection prevents component damage, but does not protect a person from high voltage.

Your safety model should predict what can still communicate or energize after a failure. Record the boundary, evidence that it holds, and the event that makes you stop.''',
'''Proposed lab A: bridged VM, default route to home router, reachable pump controller.
Proposed lab B: synthetic PLC trace, internal network, no physical I/O, snapshot.
Authorization: synthetic assets only. No real device interaction.''',
'Which proposed lab is within the stated authorization? Enter A or B.', 'b',
'Authorization and isolation both bound the experiment|A reachable device is automatically authorized|A VM cannot affect physical systems',
'Inspect routes and confirm no physical I/O is attached|Trust the virtual machine label|Run a command on the pump to see if it responds',
('If B is connected to a real actuator, what must happen?', 'Stop and reassess authorization and physical safeguards|Continue because the code is unchanged|Only rename the network'))

case(1,
'''Bits have no inherent signedness: a type and an interpretation give them meaning. Hexadecimal groups four bits per digit. An unsigned n-bit value represents 0 through 2^n−1; reduction to that width is modulo 2^n. In two’s complement, the top bit contributes a negative weight. Endianness orders bytes, not the bits within a byte. Floating point approximates many fractions, so equality and rounding require care.

Arrays give indexed contiguous storage; linked lists trade locality for explicit links. Stacks are LIFO, queues FIFO, trees hierarchical, and hash tables use a hash to choose a bucket. Complexity describes how work scales, not elapsed time on one machine.

A state machine models legal transitions. Concurrent transitions can race when a read-modify-write is not atomic. Locks serialize critical sections but can deadlock through cyclic waiting. Processes isolate address spaces; threads share an address space. Caches, RAM, filesystems, containers, and virtual machines create different layers of storage and isolation.''',
'An unsigned 8-bit counter is 250. Add 10, then store the result back into the 8-bit counter. No saturation logic exists.',
'What decimal value is stored?', '4',
'Storing into eight unsigned bits reduces the value modulo 256|Unsigned values cannot overflow|Every integer type saturates at its maximum',
'Compare 260 modulo 256 with the retained low eight bits|Change the byte order of a single byte|Measure CPU frequency',
('If the counter were unsigned 16-bit instead?', 'It would hold 260|It would still hold 4|The behavior would be undefined'))

case(2,
'''A pointer represents an address with a pointed-to type. Adding one advances by one element, not necessarily one byte. An array often converts to a pointer to its first element, but sizeof an actual array still measures the entire array. A pointer-to-pointer adds an indirection, not an extra dimension automatically. Function pointers follow a function type and ABI.

Objects have storage duration, lifetime, and bounds. Stack and heap are implementation concepts; malloc allocations need an ownership policy. Reading a freed object or dereferencing one-past an array is undefined behavior even if a test appears to work. Struct padding follows alignment requirements; unions share storage. Volatile is not a thread synchronization primitive.

Preprocessing expands macros, compilation creates assembly, assembly produces objects, and linking resolves symbols. Static/shared libraries, libc, ELF, calling conventions, and optimization all influence the final binary. Use warnings and sanitizers to collect evidence, not as proof that all undefined behavior is absent.''',
'''int a[3] = {10, 20, 30};
int *p = a;
int result = *(p + 2);
Assume sizeof(int) == 4. The first element is at address 0x1000.''',
'What decimal value is assigned to result?', '30',
'Pointer addition scales by sizeof the pointed-to type|Adding two to p moves two bytes|Array decay copies all array elements into p',
'p + 2 has address 0x1008 and refers to a[2]|sizeof(p) must equal sizeof(a)|The memory after a is readable on this run',
('What about dereferencing p + 3?', 'Undefined behavior: one-past may be formed but not dereferenced|It is guaranteed to produce zero|It reads the last element'))

case(3,
'''An instruction transforms architectural state: registers, flags, memory, and the instruction pointer. An ISA defines those effects; a microarchitecture implements them with caches, pipelines, prediction, and execution units. x86-64, ARM32, AArch64, MIPS, and RISC-V differ in encoding and conventions; never transfer a register convention without checking the ABI.

A calling convention assigns arguments, return values, and preservation duties. Stack frames commonly hold saved registers and local state, but optimization may remove a frame pointer or inline a function. Privilege levels and the MMU regulate memory access; TLBs cache address translations. Interrupts and exceptions redirect execution through defined entry paths.

Atomic instructions prevent specific interleavings. Memory ordering describes visibility between observers; an atomic operation does not automatically establish every desired ordering relationship. SIMD processes multiple lanes without changing the need to understand each instruction’s semantics.''',
'''Toy x86-64 function, System V AMD64 ABI, integer arguments:
lea eax, [rdi + rsi*2]
ret
Caller provides first argument 3 and second argument 4.''',
'What decimal integer is returned?', '11',
'LEA computes the effective-address expression without reading memory|LEA always loads the bytes at the computed address|RSI holds the first integer argument in this ABI',
'Single-step and inspect EAX after LEA|Read eleven bytes from address zero|Assume the same argument registers on ARM32',
('If the second argument becomes 5?', 'The return value becomes 13|The return value remains 11|The processor must dereference address 13'))

case(4,
'''The kernel mediates privileged operations. A syscall crosses a controlled boundary; libc may wrap it, but a library call is not necessarily a syscall. Processes have virtual address spaces backed by page tables; mappings can be private or shared. A page fault may establish a valid mapping rather than indicate a fatal error.

A file descriptor is an index into a process descriptor table. Descriptors can refer to the same open file description, sharing its offset and status flags. Pipes and sockets provide IPC. Signals notify a process asynchronously. Scheduling selects runnable tasks while synchronization constrains what tasks may safely do.

Drivers mediate devices and DMA. /proc and /sys expose runtime information. Boot flows through firmware, kernel, initramfs, and an init system. Namespaces change views, cgroups account for resources, and capabilities divide privileges; none alone is a complete security boundary.''',
'''fd = open("trace.txt", O_RDONLY); // file bytes: ABCDEF
copy = dup(fd);
read(fd, buffer, 2);             // reads AB
read(copy, buffer, 2);''',
'Which two characters does the second read return?', 'cd',
'dup refers to the same open file description and shared offset|Each descriptor always has an independent offset|read resets the offset after each call',
'Inspect offsets before and after the first read|Compare only the descriptor integer values|Check the filename extension',
('If copy came from a separate open of the file?', 'Its initial read would return AB|Its initial read would return CD|Opening the same file twice is forbidden'))

case(5,
'''Ethernet moves frames within a link; IP moves packets between networks. ARP resolves IPv4 neighbors on a local link. Routing selects a next hop, while switching forwards frames. NAT rewrites addressing and is not a substitute for an authorization policy. VLANs require enforced routing boundaries to provide segmentation.

TCP is an ordered byte stream, not a message API. UDP preserves datagram boundaries without guaranteeing delivery. Applications define framing and state above transport. DNS resolves names, DHCP supplies configuration, and TLS can authenticate peers and protect traffic when certificate validation is correct.

HTTP, MQTT, CoAP, and WebSockets have different message and session rules. Capture packets passively on your synthetic network, relate fields to protocol state, and distinguish what a trace shows from what encryption conceals. Firewalls enforce policies; IDS alerts are evidence to investigate, not proof of compromise.''',
'''A sender writes b"HELLO" then b"WORLD" to one TCP connection.
The receiver's first recv(1024) returns b"HELLOWO".
There is no packet loss. Three bytes remain in the stream.''',
'What three characters remain unread?', 'rld',
'TCP exposes bytes and recv boundaries need not match send calls|Every send creates exactly one recv message|TCP preserves application record boundaries',
'A capture and receive log show bytes split across calls|The sender used two function calls|The network uses Ethernet',
('If the application needs two records?', 'Add and parse an explicit length or delimiter framing scheme|Increase recv size to guarantee records|Use TCP packet boundaries as message delimiters'))

case(6,
'''Static analysis inspects a program without running it; dynamic analysis observes a particular execution. Disassembly decodes instructions, while decompilation reconstructs a possible high-level representation. Recovered names and types are hypotheses, especially in stripped or optimized binaries.

Follow control flow to identify branches and loops, then data flow to see where values originate and are checked. Cross-references, relocations, symbols, debug information, GOT/PLT stubs, and calling conventions help recover purpose. PE, ELF, and Mach-O encode different loader contracts. C++ virtual dispatch, RTTI, exceptions, and mangling complicate function identification.

Packers, obfuscation, and anti-analysis can hide behavior; a static absence is not proof that an action never occurs. Patch diffing and slicing narrow investigation. Symbolic and concolic execution explore paths under models that may omit environment behavior.''',
'''Recovered pseudocode (uint8 input promoted to int):
if ((x ^ 0x5a) == 0x13) return 1;
return 0;
No other input transformations occur.''',
'Which decimal x makes the function return 1?', '73|0x49',
'XOR is its own inverse, so x is 0x13 XOR 0x5a|XOR is equivalent to addition|Decompiler variable names establish original developer intent',
'Evaluate the comparison for x = 0x49 in the instruction trace|Rename x to password and trust the name|Search only printable strings',
('If 0x13 changes to 0x12?', 'The matching input changes to 0x48|The input stays 0x49|Every input now matches'))

case(7,
'''A breakpoint stops execution at an instruction; a watchpoint stops on a selected memory access or change. Hardware resources are finite, while software breakpoints often modify code bytes. Single stepping, registers, memory, and stack inspection reveal different parts of program state.

Debug symbols map machine addresses to source concepts, but optimization can remove variables or reorder instructions. A core dump captures a failure state; it does not automatically reveal the first invalid action. Work backward from symptoms to the earliest broken invariant.

ptrace, remote protocols, JTAG, SWD, and emulator-assisted debugging operate at different boundaries. Halting a real-time controller changes timing and may be unsafe; use recorded or simulated targets here.''',
'''A synthetic trace shows:
t0: count = 4
t1: count = 5
t2: unexpected writer stores count = -1
t3: array[count] causes failure
You need to stop at the write that changes count, not at the later crash.''',
'Choose the most direct tool: breakpoint, watchpoint, or core dump.', 'watchpoint',
'A data watchpoint ties the state change to the writing instruction|The crashing instruction must be the corrupting writer|Source line order always equals machine execution order',
'The stop shows the writer address and old/new count|The process has debug symbols|The executable filename mentions debug',
('If optimization keeps count only in a register?', 'Inspect disassembly and register changes; a memory watchpoint may not apply|A memory watchpoint always tracks source variables|Disable every breakpoint and guess'))

case(8,
'''Memory corruption begins with a violated object invariant: bounds, lifetime, type, or ownership. A stack or heap overflow writes outside an object; use-after-free accesses an object after its lifetime; double-free violates allocator ownership. Integer errors can create undersized allocations before the visible overwrite.

Exploitability depends on attacker control, reachable state, allocator behavior, and mitigations. NX restricts execution from data pages; ASLR and PIE vary locations; canaries detect some stack corruption; RELRO hardens relocation data; CFI, PAC, and shadow stacks constrain some control transfers. None repairs an invalid access.

Triage a synthetic crash by recording input, build, stack, sanitizer findings, and earliest invalid operation. Concepts such as ROP and return-to-libc explain why non-executable data alone is insufficient; this exercise diagnoses a toy defect rather than deploying an exploit.''',
'''char dst[8];
// length was validated only as nonnegative
memcpy(dst, input, 12);
Synthetic sanitizer report: WRITE of size 12 at dst; object size 8.''',
'How many bytes exceed the destination object?', '4',
'The copy length exceeds the destination bound regardless of NX|NX prevents all writes outside an array|A stack canary makes an oversized copy safe',
'Compare the destination object size with the actual copy length|Check only whether execution crashed|Observe that ASLR is enabled',
('If NX is enabled with identical input?', 'The out-of-bounds write still exists|The write becomes in-bounds|memcpy automatically truncates to eight bytes'))

case(9,
'''Voltage is potential difference; current is charge flow. Resistance relates voltage and current through V = IR for an ohmic element, and power is VI. Kirchhoff’s laws express conservation at nodes and loops. DC and AC describe different time behavior; a digital signal still has analog voltage, noise, and timing properties.

Pull resistors establish default levels. GPIO, PWM, ADC, and DAC connect digital computation to physical signals. Transistors switch or amplify; capacitors store charge; inductors store magnetic energy; regulators control supply voltage. Logic compatibility needs voltage limits, thresholds, and current ratings, not just matching connector shapes.

Read the datasheet and schematic before connecting anything. Ground references, signal integrity, ESD, and level shifting matter. All calculations in this lab are paper simulations; they are not instructions to work on mains or energized industrial equipment.''',
'A simulated 3.3 V supply is connected across a 330 ohm ideal resistor. Ignore other components.',
'What is the current in milliamps? Enter a number.', '10|10.0',
'Ohm’s law gives I = V / R, with units converted from amps|Current equals resistance divided by voltage|The resistor sets current independently of voltage',
'Calculate 3.3 / 330 = 0.01 A|Read the resistor color without checking supply voltage|Count the number of wires',
('If resistance doubles at the same voltage?', 'Current halves|Current doubles|Current is unchanged'))

case(10,
'''Combinational logic depends on current inputs; sequential logic also depends on stored state. Gates compose Boolean functions, multiplexers select signals, and flip-flops capture state at specified clock events. Registers and counters are collections of state elements.

Setup and hold requirements define when data must remain stable around a sampling edge. Crossing clock domains can cause metastability; synchronization reduces its probability of propagating, rather than proving it impossible. Buses combine logical protocols with electrical timing requirements.

SRAM stores state without periodic refresh while powered; DRAM needs refresh. Flash and EEPROM are nonvolatile with erase/write constraints; NAND and NOR optimize different access patterns. FPGAs and CPLDs implement configurable logic, not merely sequential software.''',
'''A positive-edge-triggered D flip-flop starts with Q = 0.
D changes to 1 while the clock is low and remains stable through the next rising edge.
Setup and hold requirements are satisfied.''',
'What is Q immediately after the rising edge settles?', '1',
'The flip-flop captures D at the active clock edge|Q continuously equals D for an edge-triggered flip-flop|A flip-flop cannot retain state',
'Compare D and Q around the rising edge on a timing trace|Inspect only the final static voltage|Count logic gates on the schematic',
('If D changes inside the setup/hold window?', 'The captured state may be unreliable because of metastability|Q is guaranteed to be 1|The entire circuit becomes nonvolatile'))

case(11,
'''Hardware investigation starts with identification: power domains, part markings, datasheets, traces, connectors, and test points. A multimeter, oscilloscope, and logic analyzer answer different questions. Digital decoding requires correct voltage thresholds and sampling assumptions.

UART is usually asynchronous serial with framing; SPI has clock and chip-select relationships; I²C uses addressing and open-drain lines. JTAG and SWD expose debug paths subject to device configuration. CAN, USB, PCIe, and storage buses differ in electrical and protocol layers. A similar-looking header is not evidence of pin compatibility.

Flash extraction and debug access must preserve original evidence and respect authorization. Fault injection and power/EM analysis study physical effects on computation; secure elements and roots of trust change which assumptions are reasonable. Use captured traces here, not live voltage or clock manipulation.''',
'''Synthetic UART capture: idle high, falling start edge, then data bits LSB first:
1 0 0 0 0 0 1 0
One high stop bit. Assume 8N1 framing and valid voltage levels.''',
'What ASCII character do the eight data bits encode? Case matters.', 'A',
'LSB-first bits form 0x41, the ASCII capital A|The first observed data bit is always the most significant|The start and stop bits are part of the ASCII byte',
'Reconstruct the weighted data bits and verify framing on adjacent bytes|Assume any idle-high line is UART|Decode without checking sampling rate',
('If you reverse the bit order assumption?', 'You would obtain 0x82 instead of 0x41|The value would stay 0x41|The stop bit becomes the parity bit'))
CASES[11]['answer_case_sensitive'] = True

case(12,
'''Microcontrollers commonly combine CPU, memory, and peripherals; a microprocessor or SoC may rely on more external components. Cortex-M and Cortex-A have different execution and system assumptions. Memory-mapped I/O lets loads and stores access peripheral registers whose semantics come from the datasheet.

Startup code establishes runtime state before application code. Interrupt vectors select handlers. Timers, DMA, GPIO, and watchdogs let hardware act asynchronously. A register may be write-one-to-clear, read-to-clear, or reserved; ordinary RAM reasoning does not always apply.

RTOS tasks share time under scheduling and synchronization constraints. Mutexes, semaphores, and queues solve different coordination problems. Worst-case interrupt latency and deadlines matter more than average throughput. Linker scripts, device trees, HALs, and board support packages describe placement and platform integration.''',
'''Simulated peripheral STATUS = 0b1010.
Bits are write-one-to-clear (W1C).
Software writes 0b0010 directly to STATUS.
No new hardware events occur during this operation.''',
'What is the remaining decimal register value?', '8|0b1000|0x8',
'Only positions written as one are cleared by W1C semantics|The write replaces the register like ordinary RAM|Writing zero clears every corresponding bit',
'Use the W1C datasheet rule and compare status before/after|Assume all registers behave like arrays|Rely only on the C variable type',
('What if software writes back the entire value 0b1010?', 'Both pending bits clear, potentially losing an event|Nothing changes|Only bit one clears'))

case(13,
'''Firmware maps software onto fixed memory and device constraints. Reset vectors and startup code initialize the machine; linker scripts place code, data, and stacks into a memory map. Drivers, interrupts, RTOS tasks, and power states must preserve timing and ownership invariants.

A reliable update is a state machine: download, verify, stage, switch, confirm, or recover. Signing authenticates an image under a trusted key; a monotonic version policy can prevent rollback. A valid signature alone says nothing about whether an image is current or compatible.

Power failure, watchdog reset, and partial writes are expected faults. A/B slots and recovery paths reduce the chance of an unbootable device. Production provisioning and key custody determine whether the verification policy remains meaningful over the device lifecycle.''',
'''Trusted device minimum version = 7.
Update version = 5, signature valid under the trusted release key.
Policy requires signature validity AND version >= minimum.
No recovery exception is enabled.''',
'Should the update be accepted or rejected?', 'rejected|reject',
'Authenticity and rollback protection are separate checks|A valid signature bypasses version policy|Older signed software cannot contain vulnerabilities',
'Compare the authenticated version to protected minimum state|Check only file size|Check only whether the file decrypts',
('If the correctly signed update were version 8?', 'It would satisfy these two checks|It would fail solely because it is newer|It should erase the minimum version first'))

case(14,
'''Firmware analysis starts by preserving an original image and hash, then identifying boundaries and formats. A package can contain a bootloader, kernel, device tree, root filesystem, configuration, and raw binary blobs. SquashFS, UBIFS, JFFS2, CramFS, and YAFFS have different storage assumptions.

Magic bytes and entropy guide hypotheses, not conclusions. High entropy can result from compression, encryption, or other data. Validate offsets, lengths, checksums, and parser success before trusting a carved object. Init scripts and configuration can reveal which code actually runs.

Hardcoded secrets, update verification, and service exposure belong in a trust-boundary analysis. Emulation may need stubs or peripheral models; successful execution of one path does not prove hardware behavior has been reproduced.''',
'''Image region starts at 0x1000.
First four bytes: 68 73 71 73 (ASCII hsqs).
A read-only parser validates the superblock and lists /etc/init.d and /bin/busybox.
A separate region has high entropy with no recognized format.''',
'Which filesystem does the validated region contain?', 'squashfs',
'Magic plus consistent structure supports identification; entropy alone does not identify encryption|High entropy always proves encryption|A four-byte match alone proves a complete valid filesystem',
'Validated superblock fields and successfully parsed directory entries|A filename ending in .bin|The image contains many nonprintable bytes',
('If only the magic matched and structure validation failed?', 'Treat the identification as unconfirmed or damaged|Declare a fully valid filesystem|Assume the firmware is malware'))

case(15,
'''An IoT system includes devices, gateways, edge computation, and backend services. Sensors report observations and actuators change the world. Provisioning establishes identity; lifecycle management must cover updates, key rotation, ownership change, and decommissioning.

MQTT is a brokered publish/subscribe protocol with topics and sessions; CoAP uses constrained request/response patterns; AMQP has different messaging semantics. BLE, Zigbee, Thread, Matter, Z-Wave, Wi-Fi, LoRaWAN, and cellular technologies trade range, bandwidth, power, and topology. GNSS provides positioning, not device authentication.

Transport protection, authenticated identity, and authorization are separate controls. A device certificate identifies a credential holder; broker policy must still constrain which topics that identity can read or write. Cloud-device trust must hold in both command and telemetry directions.''',
'''Device D1 authenticates with its own certificate over TLS.
Broker ACL: D1 may publish only to devices/D1/telemetry.
D1 tries to publish to devices/D2/commands.
The broker enforces its ACL.''',
'Is the publication allowed or denied?', 'denied|deny',
'Authenticated identity still needs resource-specific authorization|TLS grants write access to all topics|A device certificate proves ownership of every device',
'Inspect the ACL decision for D1 and the exact requested topic|Check only that the TLS handshake succeeded|Check only signal strength',
('If the broker used an allow-all ACL?', 'TLS alone would not prevent the cross-device publish|The certificate would automatically prevent it|MQTT topic names enforce ownership'))

case(16,
'''IoT security spans hardware, firmware, local protocols, mobile apps, and cloud APIs. An attack surface is an entry point plus reachable behavior; a trust boundary is where assumptions about a caller must change. Default credentials and shared secrets can turn one compromised device into a fleet problem.

Secure onboarding binds a unique identity to authorized ownership. Update verification, boot policy, and key protection must align. Local access controls must not assume that a request coming from the same LAN is trustworthy. APIs need object-level checks as well as authentication.

Plan for stolen devices, ownership transfers, revocation, and decommissioning. Erasing user data without revoking backend credentials can leave a working identity. Supply-chain and fleet controls reduce systemic impact beyond one device.''',
'''Retired device D7 is factory-reset, but its certificate remains active at the backend.
A copied private key and certificate still complete authentication.
The backend performs no additional device-lifecycle check.''',
'What backend action directly disables this credential: revoke, rename, or reboot?', 'revoke',
'Local reset does not invalidate an independently trusted backend credential|Factory reset automatically revokes all cloud certificates|Renaming a device changes its private key',
'Attempt a synthetic authentication after revocation and check rejection|Observe that local user data is gone|Read the device display name',
('If the private key is hardware-protected but the device is retired?', 'Backend revocation is still needed for lifecycle control|Retirement policy becomes unnecessary|The certificate never expires'))

case(17,
'''Frequency and wavelength are related by propagation speed. Modulation maps information onto a carrier: ASK changes amplitude, FSK frequency, PSK phase, and QAM combines amplitude and phase. OFDM divides transmission across subcarriers. Channel width, noise, antennas, and propagation constrain performance.

SNR compares signal and noise power. Decibel power ratios use 10 log10(P1/P2); adding 10 dB corresponds to a tenfold power ratio. A stronger signal does not authenticate its sender or repair a weak cryptographic protocol.

SDR separates configurable signal processing from some radio hardware. Demodulation recovers symbols before packet decoding interprets fields. BLE, Wi-Fi, Zigbee, LoRa, RFID, and NFC have distinct security models. This lab uses synthetic measurements, with no RF transmission.''',
'A synthetic RF measurement gives signal power 100 units and noise power 1 unit. Use SNR_dB = 10 * log10(signal/noise).',
'What is the SNR in dB?', '20|20.0',
'A power ratio of 100 is 20 dB on the logarithmic scale|A power ratio of 100 is always 100 dB|Higher SNR proves sender authenticity',
'Compute the power ratio before applying 10 log10|Use the carrier frequency alone|Check whether the packet has a device name',
('If noise power rises to 10 with signal unchanged?', 'SNR drops to 10 dB|SNR rises to 30 dB|SNR remains 20 dB'))

case(18,
'''A hash summarizes data but provides no authenticity by itself. HMAC combines a secret key with hashing to authenticate messages. Encryption provides confidentiality under a mode’s requirements; authenticated encryption also detects tampering. Nonces and randomness have different contracts: uniqueness may be mandatory even when secrecy is not.

Public-key systems support signatures, key agreement, and other operations. Certificates bind public keys to identities under a trust policy; verification includes chain and identity checks. Key derivation separates uses from input keying material; rotation and storage policies address lifecycle risk.

TPMs, HSMs, and secure elements protect some key operations but do not correct a bad application protocol. Secure boot needs a trusted verification chain. Side channels and implementation errors can undermine mathematically sound primitives.''',
'''Two synthetic messages are encrypted with the same stream-cipher key and nonce.
C1 = P1 XOR Kstream
C2 = P2 XOR Kstream
The observer computes C1 XOR C2.''',
'What is exposed? Enter plaintext-xor, private-key, or nothing.', 'plaintext-xor|p1 xor p2',
'The repeated keystream cancels and exposes P1 XOR P2|Nonce reuse is harmless if the nonce is public|XOR of ciphertexts always reveals the private key',
'Apply associativity and Kstream XOR Kstream = 0|Check whether ciphertext looks random|Count the key’s printable characters',
('If distinct nonces generate independent keystreams?', 'This keystream-cancellation argument no longer applies|The same plaintext XOR is necessarily exposed|Authentication becomes unnecessary'))

case(19,
'''Static malware analysis inspects metadata, code, strings, and imports; dynamic analysis observes behavior in a controlled environment. Packed or obfuscated code can hide imports and configuration. Anti-debugging and anti-VM behavior can make an empty trace inconclusive.

Behavioral analysis connects process, filesystem, persistence, and network events. Injection, hooking, shared-library loading, and syscalls are mechanisms that can have legitimate uses; context matters. A domain or hash is an indicator, not a complete explanation. YARA rules classify patterns and need false-positive testing.

Kernel and boot components carry different privileges from userland. Family clustering should combine multiple observations. This course analyzes inert event records only; the web container is not a safe execution sandbox for live malware.''',
'''Inert trace:
10:00 process sample opens /tmp/config
10:01 process writes a user autostart entry pointing to itself
10:02 process exits
There is no recorded network connection.''',
'Which behavior is directly supported: persistence, exfiltration, or kernel-rootkit?', 'persistence',
'An autostart entry supports persistence, while missing network events limit conclusions|Any autostart write proves kernel compromise|No network event proves the file is harmless',
'Correlate the entry contents, owning process, and startup mechanism|Infer exfiltration from the filename|Assume every import was executed',
('If a second run does not create the entry?', 'Investigate state and execution-path differences|Discard the first trace automatically|Conclude anti-VM behavior with certainty'))

case(20,
'''Windows processes provide address spaces and security context; threads execute within them. Handles refer to kernel-managed objects. Access tokens contain identity and privilege information, and access checks compare that context with the requested object rights.

PE headers and import data guide loading, but dynamic API resolution can hide call targets. Windows API and Native API sit at different layers. DLL search and loading, services, Registry configuration, COM, WMI, and PowerShell form both administration and analysis surfaces.

ETW and AMSI provide observations at specific boundaries; they are not complete records of all behavior. Drivers execute with different privileges. Distinguish a process name, its actual token, and the access granted to a particular handle.''',
'''Synthetic access check:
Requested right: WRITE
Object ACL: user Researcher may READ only
Process token: Researcher, no additional applicable privileges
The access check is enforced normally.''',
'Is the write request allowed or denied?', 'denied|deny',
'An authenticated token does not imply the requested object right|Every logged-in user can write every object|A process filename determines its access rights',
'Compare requested access, token, and effective ACL|Check only whether the process has a PID|Check only the PE subsystem field',
('If the process already has a legitimately granted writable handle?', 'Analyze the rights on that handle and how it was obtained|Its filename alone revokes the handle|Handles cannot carry granted rights'))

case(21,
'''Linux ELF binaries are mapped and relocated under a loader contract. For dynamically linked programs, symbol resolution can be influenced by the dynamic linker environment, including LD_PRELOAD in applicable contexts. Static linking and secure-execution rules change that behavior.

/proc exposes process state and /sys exposes kernel object information. ptrace, eBPF, and kernel modules provide different observation or extension mechanisms with privilege constraints. Capabilities divide privileged operations; namespaces change resource views; cgroups constrain resource usage.

Persistence analysis examines systemd units, cron, init scripts, loader configuration, and ownership. A suspicious file or hook is evidence to investigate, not proof of a kernel rootkit. Embedded Linux may combine a small userspace with vendor-specific boot and update behavior.''',
'''Toy dynamically linked, non-privileged process:
LD_PRELOAD=/lab/libobserve.so
libobserve.so exports puts(), recording calls before forwarding them.
The application calls puts("hello"). Loader configuration is otherwise normal.''',
'Which mechanism is demonstrated: interposition, static-linking, or paging?', 'interposition',
'The dynamic linker can resolve a symbol to a preloaded library|LD_PRELOAD edits the application source code|Every ELF binary must use the same dynamic loader',
'Inspect loaded mappings and the resolved puts target|Check only the source filename|Assume a preload always works for secure-execution binaries',
('If this program is fully statically linked?', 'Ordinary LD_PRELOAD interposition does not apply|The same preload necessarily intercepts puts|The program cannot call any function'))

case(22,
'''OT systems observe and control physical processes. PLCs and RTUs execute control functions; HMIs display state and accept operator input; SCADA supervises distributed assets; DCS integrates process control. Historians record values rather than necessarily owning control authority.

Engineering workstations configure logic. Gateways and remote I/O connect field equipment, including sensors, actuators, VFDs, relays, and motor controllers. Understanding which component measures, decides, and acts is essential to interpreting a diagram or incident.

A safety instrumented system is designed around specified safety functions and independence requirements. An HMI alarm is not automatically a safety trip. Cybersecurity changes must account for process state, availability, and tested recovery paths.''',
'''Synthetic tank architecture:
Sensor -> PLC -> inlet valve
PLC -> HMI display
Independent high-high switch -> safety controller -> separate shutdown valve
The HMI application crashes; both controllers remain healthy.''',
'Which component still executes normal inlet logic: PLC, HMI, or historian?', 'plc',
'Supervisory display and controller execution are separate functions|An HMI crash necessarily stops all controller logic|A historian directly executes every control loop',
'Inspect controller scan status and actual I/O independently of the HMI|Look only for an HMI window|Assume the display value is the physical value',
('If the PLC instead loses power?', 'Analyze actuator fail state and independent safety function|The HMI automatically becomes the PLC|A historian guarantees safe control'))

case(23,
'''Open-loop control acts without measuring its result; closed-loop control feeds the process variable back to a controller. The setpoint is desired state; the manipulated or control variable drives an actuator. PID terms react to present error, accumulated error, and error change, but tuning depends on process dynamics.

Alarms inform an operator; interlocks constrain actions; trips initiate a defined protective response. Their roles are not interchangeable. Redundancy needs common-cause analysis, and fail-safe behavior depends on the hazard: stopping a pump is not universally safe.

Availability, determinism, and physical consequences constrain experiments. Pressure, temperature, flow, and level have units and dynamics. Here, a discrete tank model illustrates cause and effect without controlling real equipment.''',
'''Synthetic tank starts at 40 L.
Inflow = 5 L per step. Outflow = 2 L per step.
Two steps occur with constant rates and no capacity limit reached.
level_next = level + inflow - outflow''',
'What is the level after two steps, in liters?', '46|46.0',
'Conservation accumulates the net flow at each step|Level equals inflow alone|A setpoint directly sets physical level instantly',
'Compare initial level with integrated inflow minus outflow|Read only the desired setpoint|Check the color of an HMI symbol',
('If inflow is set to zero for the next step?', 'Level falls to 44 L|Level immediately becomes zero|Level remains 46 L'))

case(24,
'''A common PLC scan samples inputs, executes logic, and updates outputs. The exact runtime may include asynchronous tasks and special I/O, so the scan model is an explicit assumption. Tags name data; timers, counters, and function blocks retain state under defined rules.

Ladder Logic emphasizes contacts and coils, Structured Text expresses algorithms textually, Function Block Diagram connects operations, and Sequential Function Charts describe sequences. Instruction List is a historical language. Data blocks and retentive memory affect behavior after restarts.

Online monitoring shows sampled internal state, not necessarily every transient physical event. Firmware and execution scheduling influence logic semantics. Verify interlocks and transitions against a simulated trace before treating a displayed rung as evidence of safe behavior.''',
'''Simplified scan model: input sample -> logic -> output update.
At input sample, Start = FALSE.
Immediately after sampling, physical Start becomes TRUE and remains TRUE.
Logic: Motor := Start. Initial Motor = FALSE.''',
'At this scan’s output update, is Motor true or false?', 'false|0',
'This scan uses the sampled input image from before the change|Logic automatically sees every physical change during a scan|Outputs update before inputs are sampled in this model',
'Compare physical-edge timing to the input sampling instant|Read only the final physical input|Assume all PLC runtimes have identical scan semantics',
('At the next scan, if Start is still true?', 'Motor becomes true at the output update|Motor stays false forever|The PLC must reboot first'))

case(25,
'''Industrial protocols encode process data and commands under different transport and timing assumptions. Modbus RTU adds serial framing and CRC; Modbus TCP uses an MBAP header. Register numbering in documentation can differ from zero-based protocol addresses. Vendor-specific multi-register word order must be checked.

S7, PROFINET, PROFIBUS, EtherNet/IP and CIP, OPC UA, DNP3, IEC protocols, BACnet, HART, CANopen, EtherCAT, and fieldbuses differ in object models and trust mechanisms. RS-232 and RS-485 describe electrical interfaces, not complete application authorization.

Separate a syntactically valid message from an authorized action. Legacy deployments may lack authentication. Protocol-aware monitoring must relate function, address, value, and process state. All frames in this lab are inert bytes, never sent to a controller.''',
'''Inert Modbus TCP request, hexadecimal:
00 01 00 00 00 06 01 03 00 10 00 02
MBAP = first 7 bytes. PDU = 03 00 10 00 02.
Function 03: read holding registers; next 2 bytes start address; last 2 quantity.''',
'How many registers does the request ask to read?', '2|0x2',
'The final big-endian 16-bit PDU field specifies quantity|The transaction identifier is the register quantity|Function 03 writes two registers',
'Parse PDU offsets against the function definition|Count all zero bytes|Infer authorization from valid framing',
('If the final bytes become 00 03?', 'The requested quantity becomes three registers|The start address becomes three|The frame gains authentication'))

case(26,
'''The Purdue Model describes functional levels, while zones group assets with common security needs and conduits govern communication. A diagram is a model, not an enforced firewall rule. An industrial DMZ mediates selected flows between enterprise and control networks.

Jump hosts and remote-access systems should narrow identity, time, and destination privileges. Data diodes implement a one-way communication property subject to actual architecture. Air gaps can be undermined by removable media, laptops, and hidden connections.

Asset discovery in sensitive environments often begins passively. Redundancy and deterministic traffic introduce availability constraints. Validate a zone boundary by reviewing reachable paths and required flows, not by assuming VLAN names or private addresses provide isolation.''',
'''Policy permits enterprise -> DMZ historian replica.
Policy denies enterprise -> PLC zone.
Proposed rule: allow enterprise subnet to PLC subnet, any port.
No approved exception exists.''',
'Does the proposed rule comply? Enter yes or no.', 'no',
'The rule creates a prohibited cross-zone conduit|Private IP addresses make any rule safe|A VLAN name enforces every policy automatically',
'Compare source, destination, and service with the authorized flow matrix|Check whether the subnets have different names|Rely on the diagram without checking rules',
('If only historian replication is required?', 'Permit the specific DMZ replication flow and keep PLC access denied|Allow all PLC ports temporarily forever|Remove every firewall for performance'))

case(27,
'''OT threat modeling connects entry points and trust boundaries to physical consequences. Confidentiality matters, but availability and safety can dominate response decisions. Legacy protocols and long-lived equipment often need compensating controls rather than immediate replacement.

Engineering workstation, HMI, historian, firmware, and logic changes require different evidence. Segmentation, application allowlisting, secure remote access, inventory, and configuration baselines reduce risk. A successful login does not authorize arbitrary process changes.

Incident response must coordinate with operations. Preserve evidence, verify controller and safety state, and select containment that does not create a worse hazard. Recovery engineering includes validated logic, dependencies, configuration, and restart procedures, not just restoring a disk image.''',
'''Synthetic incident: unknown engineering workstation session; logic checksum changed.
Process status is uncertain. Operations and safety staff are reachable.
Choices: A unplug every controller; B coordinate safe-state assessment and preserve evidence; C ignore because production continues.''',
'Which initial response is best supported? Enter A, B, or C.', 'b',
'Containment must account for uncertain physical state and verified safety procedures|Any cyber alert requires immediate power removal from every PLC|Continued production proves the system is uncompromised',
'Correlate authorized changes, controller logic, session records, and process state|Use the antivirus alert alone as the full root cause|Assume an unchanged HMI display proves unchanged logic',
('If a verified emergency procedure requires shutdown?', 'Follow the coordinated safety procedure with operations|Always keep production running regardless of hazard|Let the web lab directly issue shutdown commands'))

case(28,
'''Frameworks structure decisions and evidence; they are not proof that a system is secure. NIST CSF organizes cybersecurity outcomes, and SP 800-82 discusses OT-specific constraints. IEC 62443 concepts include zones, conduits, lifecycle responsibilities, and security levels. Consult the applicable edition for formal requirements.

MITRE ATT&CK for ICS describes adversary behavior and helps map detection hypotheses. A technique label does not quantify site-specific risk. Consequence-driven analysis starts from unacceptable physical outcomes and traces dependencies and safeguards.

Functional safety and cybersecurity interact but have different claims. A safety integrity level is not interchangeable with a cybersecurity security level. Defense in depth requires useful independence between controls, along with tests and evidence for each claim.''',
'''A safety component has a documented SIL target.
A project report claims this automatically proves its IEC 62443 cybersecurity security level.
No cybersecurity assessment evidence is supplied.''',
'Is that conclusion supported or unsupported?', 'unsupported',
'Safety integrity and cybersecurity assurance address different properties|SIL and security level are interchangeable numbers|Any certified component makes the whole system secure',
'Review separate cybersecurity requirements and evidence for the deployment|Copy the SIL number into the security field|Count certifications without reading their scope',
('If an ATT&CK technique is mapped to the asset?', 'Use it to refine threats and detection, not as a compliance certificate|The asset becomes automatically compliant|The technique proves an incident occurred'))

case(29,
'''Cyber-physical attack analysis follows the path from access to a process effect. Engineering software abuse, replayed commands, altered logic, sensor spoofing, and actuator manipulation operate at different trust boundaries. Legitimate administration tools can be misused without a novel binary.

A displayed process value may differ from physical state. Correlate independent sensing, controller logic, commanded outputs, and engineering change history. Safety-system interference can remove a protective layer, so evaluate dependencies rather than assuming independence from a network diagram.

Use inert traces and digital models to study these mechanisms. Establish competing hypotheses, predict observations, and preserve uncertainty. An anomalous value can also reflect sensor failure, scaling error, or delayed data.''',
'''Synthetic tank: HMI says 40 L on every sample.
Independent simulated gauge: 40, 45, 50 L.
Recorded inlet command: OPEN throughout.
No evidence yet distinguishes spoofing from stale telemetry.''',
'Which value source contradicts the constant-level claim: gauge or HMI?', 'gauge',
'Independent measurement challenges the displayed state but does not alone prove malicious cause|A constant HMI value proves the physical level is constant|Any disagreement conclusively identifies the attacker',
'Compare timestamps, independent gauge, command trace, and telemetry path|Trust the HMI because it looks normal|Assume every discrepancy is a cyberattack',
('If timestamps show the HMI data is ten minutes old?', 'Stale telemetry becomes a plausible explanation to test|Spoofing is conclusively proven|The gauge must be wrong'))

case(30,
'''Protocol reverse engineering infers structure from observations. Begin with boundaries, lengths, constants, varying fields, checksums, and sequence relationships. A packet capture is a sample of behavior; serial and RF captures add physical-layer assumptions.

Differential analysis changes one input while holding others constant. Candidate field meanings must predict new messages. Checksums and CRCs detect some corruption but do not provide cryptographic authenticity. Stateful protocols require inference of legal transitions, not just individual frame syntax.

Fuzz inferred parsers only against synthetic models or authorized isolated targets. Separate parser failures, transport faults, and peripheral-model errors. A small number of traces supports a hypothesis rather than a complete specification.''',
'''Toy frames: sync AA, length, payload, XOR checksum of payload only.
AA 02 10 20 30
AA 02 10 21 31
Proposed frame payload: 10 22 (all values hexadecimal).''',
'What checksum byte is required? Enter hexadecimal with 0x prefix.', '0x32',
'The checksum equals XOR of payload bytes under the stated framing rule|Every final byte is a cryptographic signature|The length byte must be added to the payload sum',
'Predict a held-out frame by changing only one payload byte|Assume two traces prove every protocol rule|Infer message meaning from packet color',
('If an adversary edits payload and recomputes XOR?', 'The checksum can still pass; it does not authenticate the sender|The checksum prevents intentional modification|The frame becomes encrypted'))

case(31,
'''A boot chain starts from a root whose trust must be justified, often ROM and provisioned key material. Each stage can verify the next before transferring execution. ROM, first-stage and second-stage loaders, U-Boot, BIOS, and UEFI have different platform roles.

Secure boot enforces an execution policy; measured boot records measurements for later appraisal. Attestation reports evidence under an identity and freshness policy. A TPM can protect keys and measurements, but a verifier must interpret them correctly.

Signed firmware needs version and revocation policy. TEEs and TrustZone create execution boundaries with defined interfaces; they do not make every peripheral or application trustworthy. Locate the immutable assumptions and every mutable link.''',
'''Boot design: ROM measures the next image into a protected register, then executes it regardless of its signature.
A remote verifier may later inspect the measurement.
No execution-blocking policy exists.''',
'Is this measured-boot or secure-boot enforcement?', 'measured-boot|measured boot',
'Recording a measurement is distinct from refusing unauthorized execution|Any measurement automatically blocks untrusted code|A TPM measurement proves application correctness',
'Check the control-flow decision after measurement and verification|Check only whether a hash is computed|Read only the product marketing name',
('If an untrusted image is measured?', 'It can still execute under this design|It must be blocked automatically|Its hash becomes identical to the trusted image'))

case(32,
'''Hardware security identifies assets, adversary access, trust boundaries, and physical assumptions. Debug ports may bypass software controls if production policy leaves them open. Fuses, OTP, secure elements, TPMs, and TEEs can protect specific decisions or keys under specified threat models.

External flash and buses may expose data even when CPU debug is locked. Chip-off, bus interception, cold-boot concepts, side channels, and fault injection target different physical properties. Encryption, authentication, and access control address different aspects of that exposure.

A claim such as “the key is in a secure element” needs interface and lifecycle analysis. Ask which operations are allowed, who may request them, and what happens during provisioning, reset, update, and recovery.''',
'''Design A locks SWD in production but stores an API secret as plaintext in external flash.
An authorized investigator receives an offline copy of that flash.
No live extraction or hardware interaction occurs.''',
'Is the secret protected by the SWD lock in this copy? Enter yes or no.', 'no',
'Debug-port access control does not encrypt independent external storage|Locking SWD encrypts every peripheral automatically|A secret is safe whenever it is not printed on a label',
'Inspect the flash representation and storage threat model|Check only the debug-lock fuse|Assume all chips share one access boundary',
('If the flash is authenticated but not encrypted?', 'Integrity protection alone still does not hide the secret|Authentication provides confidentiality automatically|The secret is deleted'))

case(33,
'''Hardware virtualization runs guest code with hardware support; emulation models an ISA or a larger machine in software. QEMU user-mode emulation supplies an execution environment for a process, while system emulation includes a machine model. Neither automatically reproduces every device.

Snapshots preserve a defined subset of state. Disk snapshots alone may omit RAM, peripheral state, backend services, or clocks. Instrumentation reveals behavior within the model, which may differ from physical hardware.

Firmware emulation and digital twins trade fidelity against observability and cost. ICS simulation can test control hypotheses without physical actuation. Document model boundaries so a passing simulation is not mistaken for validated plant behavior.''',
'''A toy emulator snapshot restores CPU, RAM, and disk.
Its external simulated sensor service retains a monotonically increasing counter.
Run 1 sees counter 10. After restore, Run 2 sees counter 11.''',
'Which state was omitted: sensor, RAM, or CPU?', 'sensor',
'Reproducibility requires all causally relevant state, including external services|A disk snapshot always resets the entire world|Different input proves the CPU emulator is broken',
'Record and reset the external sensor counter along with the snapshot|Compare only disk hashes|Restart the browser without resetting services',
('If the sensor is replaced with a deterministic recorded stream?', 'Replay can become repeatable within the documented model|Hardware fidelity is automatically perfect|Timing no longer matters in any system'))

case(34,
'''A control-flow graph represents possible transfers between blocks; a data-flow graph tracks value relationships. Call graphs connect functions. SSA gives each assignment a distinct name and merges paths through phi-like operations, helping analysis reason about definitions.

Taint analysis tracks influence from selected sources to sinks under explicit propagation and sanitization rules. Symbolic execution expresses path conditions; constraint solvers search for satisfying inputs. Abstract interpretation computes approximations that trade precision for tractability.

Program slicing isolates statements relevant to a value. Static analysis considers modeled paths; dynamic instrumentation records executed behavior. Coverage counts what was observed under a metric, not whether every semantic bug was found.''',
'''Toy program:
x = untrusted_input()
y = x + 1
if y < 8:
    array[y] = 0
array has indices 0 through 7; x is an unbounded signed integer.
Consider x = -2.''',
'What index is written for this input?', '-1',
'The upper-bound check does not establish the missing lower bound|Any comparison sanitizes a tainted value|Taint means a value is always malicious',
'Trace x = -2 through y = -1 and the satisfied branch|Inspect only the true branch label|Count the number of checks without their predicates',
('If the guard becomes 0 <= y < 8 in mathematical pseudocode?', 'The negative index path is excluded by the guard|The same negative index still passes|All possible program bugs are now eliminated'))

case(35,
'''A fuzzing harness exposes a narrow target with repeatable setup and observable failures. Mutation fuzzing changes existing samples; generation and grammar fuzzing construct structured inputs. Coverage-guided fuzzing uses execution feedback to prioritize exploration, not to prove correctness.

Firmware, protocol, snapshot, and hardware-in-the-loop fuzzing add state and environment constraints. Reset between cases to avoid misleading nondeterminism. A corpus should retain useful diversity while minimizing redundant samples.

Crashes need reproduction, deduplication, minimization, and root-cause analysis. Stack hashes are useful clues but not perfect bug identities. Sanitizers can reveal violations before a visible crash. Preserve builds, seeds, environment, and the minimized reproducer.''',
'''Toy parser crashes whenever a byte string contains FF 00 as adjacent bytes.
Original input: AA BB FF 00 CC DD.
All other bytes are irrelevant in this explicit toy model.''',
'Give the minimal reproducer as two space-separated hex bytes.', 'ff 00|ff00',
'Minimization preserves the failure while removing irrelevant input|The shortest file always exercises the most code|Every crashing input represents a unique bug',
'Replay FF 00 and verify neither single-byte deletion still fails|Keep only a screenshot of the crash|Assume a fuzzer crash never needs reproduction',
('If the minimized input stops failing on a clean restart?', 'Investigate hidden state or nondeterminism before claiming a stable reproducer|Publish it as fully reproducible anyway|Conclude the vulnerability is fixed'))

case(36,
'''Python is useful for automation and binary analysis because bytes, slicing, and libraries expose data transformations clearly. struct requires explicit format assumptions: byte order, field size, and alignment. Python integers do not normally wrap like fixed-width machine integers, so model width deliberately.

Sockets and serial interfaces deliver data under transport-specific rules. Parsers must validate lengths before unpacking, account for partial input, and bound resource use. ELF/PE and firmware parsing need format validation rather than trusting filenames.

Debugger and disassembler scripts should preserve provenance and report uncertainty. A fuzzing harness needs deterministic reset behavior. The practice tools here process inert data; submitted Python source is stored as evidence and is never executed by the web server.''',
'''import struct
blob = bytes.fromhex("34 12")
value = struct.unpack("<H", blob)[0]
< means little-endian; H means unsigned 16-bit.''',
'What decimal value is decoded?', '4660|0x1234',
'The first byte is the low-order byte in this explicit little-endian format|Python guesses endianness from the file extension|H always means signed 32-bit',
'Compute 0x34 + (0x12 << 8)|Use the host CPU architecture instead of the format|Decode bytes as UTF-8 text',
('If the format changes to >H?', 'The value becomes 0x3412|The value remains 0x1234|The data gains two bytes'))

case(37,
'''Engineering discipline makes research reproducible. Version control records change history; build systems capture transformation rules; dependency locks constrain inputs. Reproducible builds require more than source alone: toolchains, environment, timestamps, and configuration can affect artifacts.

Unit tests target small contracts, integration tests exercise boundaries, and CI repeats checks in a defined environment. Logging supports diagnosis, profiling locates resource costs, and static analysis finds selected classes of defects. None substitutes for understanding the system contract.

API design, review, documentation, and secure coding should expose invariants and failure behavior. A useful bug report includes the reproducer, expected and observed behavior, and the exact revision and build settings.''',
'''Build A: same source revision, compiler X version 1, dependencies locked.
Build B: same source revision, compiler X version 2, dependencies floating.
The binaries have different hashes.''',
'Is identical source alone enough to promise identical binaries? Enter yes or no.', 'no',
'Toolchain and dependency inputs can change generated artifacts|A Git commit controls every build input automatically|Different hashes always prove malicious modification',
'Compare toolchain versions, lockfiles, flags, and environment|Compare only source directory names|Assume build timestamps can never matter',
('If all declared inputs match but hashes still differ?', 'Investigate undeclared inputs and nondeterminism|Ignore the mismatch|Conclude all tests must be invalid'))

case(38,
'''Threat modeling identifies assets, actors, entry points, trust boundaries, and unwanted outcomes. Least privilege minimizes authority; defense in depth combines useful controls with understood dependencies. Authentication identifies a caller, while authorization evaluates a requested action on a resource.

Secrets and keys need generation, storage, distribution, rotation, and revocation policies. Secure update and boot architectures rely on trust anchors and recovery. Provisioning and supply-chain controls determine the integrity of initial state.

An SBOM inventories software components; it does not prove those components are safe or that a listed vulnerability is reachable. Vulnerability management needs context, ownership, validation, and a response plan.''',
'''User A authenticates correctly.
Request: GET /devices/B/secrets
Service checks only “is logged in” and returns B’s secret.
Policy: a user may access secrets only for devices they own.''',
'Which control is missing: authentication or authorization?', 'authorization',
'Identity must be checked against ownership of the requested object|A valid login authorizes every resource|Changing a URL is inherently an authentication failure',
'Test two distinct users against both owned and unowned device IDs|Test only an anonymous request|Hide the device identifier in the UI',
('If IDs become random UUIDs but checks remain absent?', 'The authorization flaw remains|The flaw is necessarily fixed|Authentication is no longer needed'))

case(39,
'''Research begins with a scoped target and an attack-surface map. Identify entry points, trust boundaries, and data flows before choosing source, binary, firmware, protocol, or hardware auditing techniques. Fuzzing and differential testing provide observations that must be explained.

A crash is a symptom. Root-cause analysis locates the earliest invariant violation; exploitability assessment asks what control and consequences are actually supported. Patch diffing can reveal a changed guard, but the surrounding semantics still need inspection.

A useful disclosure includes affected versions, reproducible evidence, root cause, impact with limits, and a suggested fix or mitigation. CWE categorizes weaknesses; CVE identifies particular disclosed vulnerabilities under its process. Coordinate disclosure with the authorized owner rather than claiming untested impact.''',
'''Toy patch:
Before: if (n <= 8) copy(dst8, src, n + 1);
After:  if (n < 8)  copy(dst8, src, n + 1);
Assume n is nonnegative and copy writes exactly n + 1 bytes.''',
'Which decimal n exposes the original boundary error?', '8',
'The old guard allows nine bytes into an eight-byte destination|Changing <= to < always fixes every vulnerability|Any crash proves arbitrary code execution',
'Reproduce n = 8 and compare write length with destination size|Claim remote compromise from the diff alone|Test only n = 0',
('What further boundary assumption needs checking in real C code?', 'Integer ranges and overflow in n + 1, plus caller and object contracts|Only the source filename|Whether the patch author used a short commit message'))

case(40,
'''Boolean algebra models predicates and logic circuits; modular arithmetic models fixed-width wraparound and underlies many cryptographic constructions. Number theory and finite fields describe different algebraic structures, so ordinary integer intuition does not always transfer.

Probability assigns likelihood under a model; statistics estimates properties from samples. Independence is an assumption to justify. Entropy quantifies uncertainty of a distribution, not whether a particular file “looks random.” Information theory connects coding and communication limits.

Graphs model control flow and dependencies. Discrete mathematics supports state exploration. Signal-processing mathematics connects sampling, frequency, and transformations; a sample rate and model determine what can be inferred from a captured signal.''',
'A fair independent 8-bit random value is drawn once. A guess is fixed before the draw. Every value 0 through 255 has equal probability.',
'What is the probability of a correct guess? Enter a fraction.', '1/256',
'Uniform eight-bit uncertainty gives 256 equally likely outcomes|Eight bits give only eight possible outcomes|An apparently random value is guaranteed unpredictable under every process',
'Count the equally likely outcomes under the stated distribution|Inspect one output and declare uniformity|Count the number of hexadecimal letters',
('If only 16 values are possible and equally likely?', 'A valid fixed guess succeeds with probability 1/16|The probability stays 1/256|The probability becomes zero'))

case(41,
'''Research notes separate observations, interpretations, and hypotheses. A hypothesis makes a prediction that could be wrong. A controlled experiment changes one relevant variable while documenting what is held constant; replication checks whether the result is stable.

Datasheets, manuals, standards, RFCs, patents, source history, and binary-to-source comparisons answer different questions. Record exact versions and sections. Normative requirements differ from examples, and implementation behavior can differ from a specification.

A technical report should let another researcher reproduce the observation and understand uncertainty. Keep timestamps, artifacts, build identifiers, tools, commands, expected behavior, and limitations. An honest disconfirming result improves a mental model.''',
'''Hypothesis: changing field X alone causes parser rejection.
Experiment A changes X and packet length; rejection occurs.
Experiment B changes only X, keeps a valid length and every other byte fixed; rejection occurs.
Both observations are repeatable in the synthetic parser.''',
'Which experiment better isolates X? Enter A or B.', 'b',
'Controlling other variables reduces competing explanations|Two simultaneous changes identify a unique cause|A hypothesis is valid only when it cannot be falsified',
'Compare a baseline with a one-variable intervention and repeat it|Collect only supporting screenshots|Omit unsuccessful trials from the journal',
('If a later controlled trial accepts the changed X?', 'Revise the hypothesis and investigate additional conditions|Delete the trial because it disagrees|Treat the original claim as certain'))
