import std.io;
 
enum SubPacketHeaders : u8 {
    hid_key_down = 0x81,
    hid_key_up = 0x01,
    delay = 0x0f,
    mouse_down = 0x88,
    mouse_up = 0x08,
    mouse_scroll = 0x05,
    mouse_move = 0x09
};

enum loopTypes: u8{
    loop_until_stop_press = 0x20,
    loop_until_any_click = 0x40,
    loop_until_trigger_key_is_pressed_again_IDK = 0x60,
    loop_for_no_loops = 0x00
}; 
 
enum MouseClick : u16 {
    left_click = 0x01,
    right_click = 0x02,
    middle_click = 0x04,
    forward = 0x10,
    backward = 0x08
};

// Unlike many other events this is a toggle
enum MouseScroll : u16 { 
    scroll_up = 0x03,
    scroll_down = 0xFD
};
 
 /* --------------------------------- */

bitfield header {
    hid_report_id :8;
    command_type :8;
    u8 slot;
    padding:8;             // Unknown
    u16 payload_length;    // Little Endian
    u16 no_loops;
    loopTypes loop_type;
    u16 time_delay;
    u16 instruct_count;    // Number of instructions
    padding: 24; 
    
 };
 
 
 bitfield sub_HID {
    u8 hid_key;
    padding: 8;
 };
 
 bitfield sub_delay {
    u16 delay; //Little Endian
 };
 

bitfield sub_mouse {
    MouseClick click; //Little Endian
 };
 
 bitfield sub_mouse_scroll {
    MouseScroll scroll; //Little Endian
 };
 
 bitfield sub_mouse_move {
    s8 x;
    s8 y; //Note that Y is reversed pos = down, neg = up
 };
 
 bitfield macro_sub_packet {
    SubPacketHeaders id;
    match(id){
        (SubPacketHeaders::hid_key_down): sub_HID key_down;
        (SubPacketHeaders::hid_key_up): sub_HID key_up;
        (SubPacketHeaders::delay): sub_delay delay;
        (SubPacketHeaders::mouse_down): sub_mouse mouse_down;
        (SubPacketHeaders::mouse_up): sub_mouse mouse_up;
        (SubPacketHeaders::mouse_scroll): sub_mouse_scroll mouse_scroll;
        (SubPacketHeaders::mouse_move): sub_mouse_move mouse_move; 
    }  
    padding: 8;
 };
 
 struct Pattern {
     header headers;
     std::print(headers.instruct_count);
     macro_sub_packet packets[12];

 };
 
 Pattern short_macro_packet @ 0x00;
 u16 ending @ 0x3E;