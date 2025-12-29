#include <stdio.h>
#include "pico/stdlib.h"
#include "pico/time.h"   // For repeating_timer
#include "pico/double.h" // For cos()

#include "tusb.h"
#include "tusb_config.h"

// --- Simple ring buffer for produced data ---
#define RING_SIZE (8 * 1024)
static_assert((RING_SIZE & (RING_SIZE - 1)) == 0, "RING_SIZE must be a power of two");

static uint8_t ring[RING_SIZE];
static volatile uint32_t ring_head = 0; // Write index
static volatile uint32_t ring_tail = 0; // Read index
static inline uint32_t ring_available_write(void) {
    if (ring_head >= ring_tail) return RING_SIZE - (ring_head - ring_tail) - 1;
    return (ring_tail - ring_head) - 1;
}
static inline uint32_t ring_available_read(void)
{
    if (ring_head >= ring_tail) return (ring_head - ring_tail);
    return RING_SIZE - (ring_tail - ring_head);
}
static inline void ring_write_byte(uint8_t b) {
    if (ring_available_write() == 0) return; // Drop if full
    ring[ring_head] = b;
    ring_head = (ring_head + 1) & (RING_SIZE - 1); // Reason why RING_SIZE must be a power of 2
}
static inline uint32_t ring_read(uint8_t *dst, uint32_t max_len) {
    uint32_t avail = ring_available_read();
    if (avail == 0) return 0;
    if (avail > max_len) avail = max_len;
    for (uint32_t i = 0; i < avail; ++i) {
        dst[i] = ring[ring_tail];
        ring_tail = (ring_tail + 1) & (RING_SIZE - 1); // Reason why RING_SIZE must be a power of 2
    }
    return avail;
}

// --- Simple data producer - cosine wave with 2s period ---
static repeating_timer_t producer_timer;
static uint8_t sample_value = 0;
static uint8_t sample_count = 0;
bool producer_cb(repeating_timer_t *rt) {
    sample_value = (uint8_t) (255.0f/2.0f*(cos(3.14f*0.01f*sample_count) + 1.0f));
    ring_write_byte(sample_value);
    sample_count = (sample_count < 200) ? ++sample_count : 0;
    return true;
}

// --- Try to send one packet of up to 64 bytes ---
static void usb_try_send_stream(void) {
    if (!tud_vendor_mounted()) return;
    if (!tud_vendor_write_available()) return; // Endpoint buffer busy
    uint8_t buf[64];
    uint32_t n = ring_read(buf, sizeof(buf));
    if (n == 0) return; // No data yet
    uint32_t written = tud_vendor_write(buf, n);
    (void)written;
    tud_vendor_flush(); // Hand off to USB controller
}

int main()
{
    stdio_init_all();

    // Bring up the TinyUSB stack
    tusb_rhport_init_t dev_init = { 
        .role  = TUSB_ROLE_DEVICE,
        .speed = TUSB_SPEED_FULL
    };
    tusb_init(0, &dev_init);

    while (!tusb_inited()) 
        sleep_ms(1);

    add_repeating_timer_ms(10, producer_cb, NULL, &producer_timer);

    while (true) {
        tud_task();

        if (tud_ready())
        {
            if (tud_vendor_write_available() >= 64)
            {
                usb_try_send_stream();
            }
        }
    }
}
