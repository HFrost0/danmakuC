#include <cmath>
#include "ass.h"
#include <iostream>
#include <fmt/core.h>
#include <boost/algorithm/string.hpp>
#include <codecvt>

using namespace std;

std::size_t utf8_len(const std::string& utf8) {
    return std::wstring_convert<std::codecvt_utf8<char32_t>, char32_t>{}.from_bytes(utf8).size();
}

int find_alternative_row(vector<vector<Comment*>>& rows, Comment& c, int height, int reserve_blank) {
    int res = 0;
    for (int row = 0; row < height - reserve_blank - ceil(c.part_size); ++row) {
        if (rows[c.mode][row] != nullptr)
            return row;
        else if (rows[c.mode][row]->progress < rows[c.mode][res]->progress)
            res = row;
    }
    return res;
}

void mark_comment_row(vector<vector<Comment*>>& rows, Comment& c, int row) {
    for (int i = row; i < row + ceil(c.part_size) && i < rows[0].size(); ++i)
        rows[c.mode][i] = &c;
}

int test_free_row(vector<vector<Comment*>>& rows, Comment& c, int row, int width, int height,
                  int reserve_blank, float duration_marquee, float duration_still) {
    int res = 0;
    int row_max = height - reserve_blank;
    Comment* target_row = nullptr;
    if (c.mode == 1 || c.mode == 2) {
        while (row < row_max && res < c.part_size) {
            if (target_row != rows[c.mode][row]) {
                target_row = rows[c.mode][row];
                if (target_row != nullptr && target_row->progress + duration_still > c.progress)
                    break;
            }
            row++;
            res++;
        }
    } else {
        int div = c.max_len + width;
        float threshold_time;
        if (div != 0)
            threshold_time = c.progress - duration_marquee * (1 - width / float (div));
        else
            threshold_time = c.progress - duration_marquee;
        while (row < row_max && res < c.part_size) {
            if (target_row != rows[c.mode][row]) {
                target_row = rows[c.mode][row];
                div = target_row->max_len + width;
                if (div != 0 && (target_row->progress > threshold_time ||
                                 target_row->progress + target_row->max_len * duration_marquee / div > c.progress))
                    break;
            }
            row++;
            res++;
        }
    }
    return res;
}

vector<float > get_zoom_factor(vector<int>& source_size, vector<int>& target_size) {
    float source_aspect = float (source_size[0]) / source_size[1];
    float target_aspect = float (target_size[0]) / target_size[1];
    if (target_aspect < source_aspect) {  // narrower
        if (source_size[0] == 0 || source_aspect == 0) return {1, 0, 0};
        float scale_factor = float (target_size[0]) / source_size[0];
        return {scale_factor, 0, (target_size[1] - target_size[0] / source_aspect) / 2};
    } else if (target_aspect > source_aspect) {  // wider
        if (source_size[1] == 0) return {1, 0, 0};
        float scale_factor = target_size[1] / source_size[1];
        return {scale_factor, (target_size[0] - target_size[1] * source_aspect) / 2, 0};
    } else {
        if (source_size[0] == 0) return {1, 0, 0};
        return {float (target_size[0]) / source_size[0], 0, 0};
    }
}

string ass_escape(const string& s) {
    // todo
    return s;
}

int clip_byte(float x) {
    if (x > 255) return 255;
    else if (x < 0) return 0;
    else return round(x);
}

string convert_color(int RGB, int width = 1280, int height = 576) {
    if (RGB == 0x000000)
        return "000000";
    else if (RGB == 0xFFFFFF)
        return "FFFFFF";
    int R = (RGB >> 16) & 0xFF;
    int G = (RGB >> 8) & 0xFF;
    int B = RGB & 0xFF;
    if (width < 1280 and height < 576)
        return fmt::format("{:02X}{:02X}{:02X}", B, G, R);
    else
        return fmt::format("{:02X}{:02X}{:02X}",
                           clip_byte(R * 0.00956384088080656 + G * 0.03217254540203729 + B * 0.95826361371715607),
                           clip_byte(R * -0.10493933142075390 + G * 1.17231478191855154 + B * -0.06737545049779757),
                           clip_byte(R * 0.91348912373987645 + G * 0.07858536372532510 + B * 0.00792551253479842)
        );
}

string convert_progress(float progress) {
    float timestamp = round(progress * 100.0);
    auto [hour, x1] = div(timestamp, 360000);
    auto [minute, x2] = div(x1, 6000);
    auto [second, centsecond] = div(x2, 100);
    return fmt::format("{}:{:02d}:{:02d}.{:02d}", hour, minute, second, centsecond);
}

int convert_type2(int row, int height, int reserve_blank) {
    return height - reserve_blank - row;
}

class AssText {
public:
    int width;
    int height;
    int reserve_blank;
    std::string font_face;
    float font_size;
    float alpha;
    float duration_marquee;
    float duration_still;
    bool reduced;
    // others
    vector<Comment>& comments;
    vector<int> bili_player_size;
    vector<float > zoom_factor;
    string text;

    AssText(int w, int h, int rb, std::string ff, float fs, float a, float dm, float ds, bool rd,
            std::vector<Comment>& cs) :
            width(w), height(h), reserve_blank(rb), font_size(fs), font_face(ff), alpha(a), duration_marquee(dm),
            duration_still(ds), reduced(rd), comments(cs) {
        text = fmt::format("[Script Info]\n"
                           "; Script generated by danmakuC (based on Danmaku2ASS)\n"
                           "; https://github.com/HFrost0/danmakuC\n"
                           "Script Updated By: danmakuC (https://github.com/HFrost0/danmakuC)\n"
                           "ScriptType: v4.00+\n"
                           "PlayResX: {0}\n"
                           "PlayResY: {1}\n"
                           "Aspect Ratio: {0}:{1}\n"
                           "Collisions: Normal\n"
                           "WrapStyle: 2\n"
                           "ScaledBorderAndShadow: yes\n"
                           "YCbCr Matrix: TV.601\n"
                           "\n"
                           "[V4+ Styles]\n"
                           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
                           // todo stylid
                           "Style: danmakuC, {2}, {3:.0f}, &H{4:02X}FFFFFF, &H{4:02X}FFFFFF, &H{4:02X}000000, &H{4:02X}000000, 0, 0, 0, 0, 100, 100, 0.00, 0.00, 1, {5:.0f}, 0, 7, 0, 0, 0, 0\n"
                           "\n"
                           "[Events]\n"
                           "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n",
                           width, height, font_face, font_size, int(round(1 - alpha)) * 255,
                           max(font_size / 25.0, 1.0));
        // bili_player_size = {512, 384}  // Bilibili player version 2010
        // bili_player_size = {540, 384}  // Bilibili player version 2012
        // bili_player_size = {672, 438}  // Bilibili player version 2014
        bili_player_size = {891, 589};    // Bilibili player version 2021 (flex)
        vector<int> target_size{width, height};
        zoom_factor = get_zoom_factor(bili_player_size, target_size);
        handle_comments();
        for (int i = 0; i < comments.size(); ++i) {
            Comment& c = comments[i];
            if (c.mode != 4)
                write_comment(c);
            else
                write_bilipos_comment(c);
        }
    }

    string to_string() { return text; }

    float get_position(float input_pos, bool is_height) {
        if (input_pos > 1)
            return zoom_factor[0] * input_pos + zoom_factor[is_height + 1];
        else
            return bili_player_size[is_height] * zoom_factor[0] * input_pos + zoom_factor[is_height + 1];
    }

    void write_bilipos_comment(Comment& c) {
        // todo
        return;
    }

    void write_comment(Comment& c) {
        string content = ass_escape(c.content);
        vector<string> styles;
        float duration;
        switch (c.mode) {
            case 1: {
                styles.push_back(fmt::format("\\an8\\pos({}, {})",
                                             width / 2, c.row));
                duration = duration_still;
                break;
            }
            case 2: {
                styles.push_back(fmt::format("\\an2\\pos({}, {})",
                                             width / 2, convert_type2(c.row, height, reserve_blank)));
                duration = duration_still;
                break;
            }
            case 3: {
                styles.push_back(fmt::format("\\move({2}, {1}, {0}, {1})",
                                             width, c.row, -ceil(c.max_len)));
                duration = duration_marquee;
                break;
            }
            default: {
                styles.push_back(fmt::format("\\move({0}, {1}, {2}, {1})",
                                             width, c.row, -ceil(c.max_len)));
                duration = duration_marquee;
            }
        }
        float size = c.size - font_size;
        if (size <= -1 || size >= 1)
            styles.push_back(fmt::format("\\fs{:.0f}", c.size));
        if (c.color != 0xFFFFFF) {
            styles.push_back(fmt::format("\\c&H{}&", convert_color(c.color)));
            if (c.color == 0x000000)
                styles.push_back("\\3c&HFFFFFF&");
        }
        text += fmt::format("Dialogue: 2,{0},{1},danmakuC,,0000,0000,0000,,{{{2}}}{3}\n",
                            convert_progress(c.progress),
                            convert_progress(c.progress + duration),
                            boost::algorithm::join(styles, ""),
                            content
        );
    }

    void handle_comments() {
        /// sort first
        sort(comments.begin(), comments.end(), [](Comment& a, Comment& b) -> bool {
            if (a.progress != b.progress)
                return a.progress < b.progress;
            else
                return a.ctime < b.ctime;
        });

        /// fill extra field
        for (int idx = 0; idx < comments.size(); ++idx) {
            Comment& i = comments[idx];
            if (i.mode != 4) {
                i.size = int(i.font_size) * font_size / 25.0;
                vector<string> parts;
                boost::split(parts, i.content, boost::is_any_of("\n"));
                i.part_size = i.size * parts.size();
                int max_len = 0;
                for (string& p: parts) {
                    int part_len = utf8_len(p);
                    if (part_len > max_len)
                        max_len = part_len;
                }
                i.max_len = max_len * i.size;
            } else
                i.size = i.font_size, i.part_size = 0, i.max_len = 0;
        }

        /// find row
        vector<vector<Comment*>> rows(4, vector<Comment*>(height - reserve_blank + 1, nullptr));
        for (int idx = 0; idx < comments.size(); ++idx) {
            Comment& c = comments[idx];
            if (c.mode != 4) {  // not a bilipos
                int row = 0;
                int row_max = height - reserve_blank - c.part_size;
                bool flag = true;
                while (row <= row_max) {
                    int free_row = test_free_row(rows, c, row,
                                                 width, height, reserve_blank, duration_marquee, duration_still);
                    if (free_row >= c.part_size) {
                        mark_comment_row(rows, c, row);
                        flag = false;
                        break;
                    } else
                        row += 1;  // todo row += freerows || 1;
                }
                if (flag && reduced) {
                    row = find_alternative_row(rows, c, height, reserve_blank);
                    mark_comment_row(rows, c, row);
                }
                c.row = row;
            }
        }
    }
};

string comments2ass(vector<Comment>& comments,
                    int width,
                    int height,
                    int reserve_blank,
                    std::string font_face,
                    float font_size,
                    float alpha,
                    float duration_marquee,
                    float duration_still,
                    bool reduced) {
    AssText ass(width, height, reserve_blank, font_face, font_size, alpha, duration_marquee, duration_still, reduced,
                comments);
    return ass.to_string();
}

