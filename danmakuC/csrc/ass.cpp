#include <map>
#include <cmath>
#include <codecvt>
#include <regex>
#include <fstream>
#include <fmt/core.h>
#include <pybind11/pybind11.h>
#include <boost/algorithm/string.hpp>


using namespace std;


class Comment {
public:
    float progress;
    float duration;
    int ctime;
    string content;
    int mode;
    int pool;
    // override tags
    string font;
    float size;
    int color;
    float alpha;
    // others
    float vpos;
    float part_size;
    float max_len;
    int row;
    int lines = 1;
    int align = 0;
    float delta_l = 0;

    Comment() = delete;

    Comment(float progress,
            float duration,
            int ctime,
            string content,
            int mode,
            int pool,

            string font,
            float size,
            int color,
            float alpha
    ) : progress(progress), duration(duration), ctime(ctime), content(content), mode(mode), pool(pool),
        font(font), size(size), color(color), alpha(alpha) {
            vpos = progress;
        }

    // https://w.atwiki.jp/commentart2/pages/31.html
    void resize(int height, bool full, bool ender) {
        int width = full ? height * 16.0/9.0 : height * 4.0/3.0;
        float r = 1.0;
        bool vertical_resize;
        bool horizen_resize;

        vertical_resize = ender ? false : part_size > height/3.0;
        if (vertical_resize)
            r = 0.5;
        horizen_resize = (mode==1 || mode==2) ? max_len * r > width : false;
        if (vertical_resize && horizen_resize)
            return;
        if (!vertical_resize && !horizen_resize)
            return;
        if (horizen_resize)
            r = width / max_len;
        
        size *= r;
        max_len *= r;
        part_size *= r;
    }
    
    // https://w.atwiki.jp/commentart2/pages/39.html
    void retime(int width, int height, float dm) {
        /*
            The duration of scrolling comments on Niconico are based
            on the 4:3 aspect ratio, regardless of the actual stage width.
            Using the vpos attribute as the reference time 0, a comment
            first appears at the edge of the stage (in 4:3 mode) at time 0 - t.
            When a comment is sent, it appears at a position that has already
            traveled a certain distance, and this is considered time 0.

            For normal scrolling comments, t equals 1 seconds. However, it is unclear
            whether t remains 1 for comments with a specified duration (via an @ command),
            or how it is calculated if not.
            (Based on my personal testing, t=1 gives the most accurate result.)
            Anyway, a retime is needed when converting a Niconico comment file to ASS.
            Additionally, an extra delta_l needs to be calculated in the following two cases:
            1. At the start of the video
            2. Near the end of the video (a video length parameter is required)
        */
        float t = 1;
        int width_43 = height * 4.0 / 3;
        float speed = (width_43 + max_len) / (duration + t);
        duration = (width + max_len) / speed;
        float dt = 0.5 * (width - width_43) / speed + t;
        if (progress >= dt)
            progress -= dt;
        else {
            delta_l = (dt - progress) * speed;
            duration -= dt - progress;
            progress = 0;
        }

        // todo: reverse
        /*
        if (mode == 3) {
            // not always l-to-r
            if ((reverse_start > 0 && reverse_end > 0) || !(vpos >= reverse_start && vpos_end <= reverse_end))  { 
                // r-to-l, then l-to-r
                if (vpos < reverse_start && vpos_end <= reverse_end) {
                    duration = (reverse_start - progress) * 2;
                }
                // l-to-r, then r-to-l
                else if (vpos >= reverse_start && vpos_end > reverse_end) {
                    duration = (reverse_end - progress) * 2;
                }
                // r-to-l, then l-to-r, finally r-to-l
                else {
                    duration += (reverse_end - reverse_start) * 2;
                }
            }
        }*/
    }
};

size_t utf8_len(const string& utf8) {
    return wstring_convert<codecvt_utf8<char32_t>, char32_t>{}.from_bytes(utf8).size();
}

int find_alternative_row(vector<vector<Comment*>>& rows, Comment& c, int height, int reserve_blank) {
    int res = 0;
    for (int row = 0; row < height - reserve_blank - ceil(c.part_size); ++row) {
        if (rows[c.mode][row] == nullptr)
            return row;
        else if (rows[c.mode][row]->progress < rows[c.mode][res]->progress)
            res = row;
    }
    return res;
}

void mark_comment_row(vector<vector<Comment*>>& rows, Comment& c, int row) {
    for (size_t i = row; i < row + ceil(c.part_size) && i < rows[0].size(); ++i)
        rows[c.mode][i] = &c;
}

void unmark_rows(vector<vector<Comment*>>& rows, int mode) {
    for (size_t i = 0; i < rows[mode].size(); ++i)
        rows[mode][i] = nullptr;
}

int test_free_row(vector<vector<Comment*>>& rows, Comment& c, int row, int width, int height, int reserve_blank) {
    int res = 0;
    int row_max = height - reserve_blank;
    Comment* target_row = nullptr;
    if (c.mode == 1 || c.mode == 2) {
        while (row < row_max && res < c.part_size) {
            if (target_row != rows[c.mode][row]) {
                target_row = rows[c.mode][row];
                // Niconico appears to allow a slight overlap for still comments
                // Example: https://www.nicovideo.jp/watch/sm31436903
                // Refer to 2:18 ~ 2:21, comment no.415 ("に") and no.433 ("に"), vpos: 138.80s and 141.71s, duration: 3.0s
                // Set the tolerance to 0.1s for now
                if (target_row != nullptr && target_row->progress + target_row->duration - 0.1 > c.progress)
                    break;
            }
            row++;
            res++;
        }
    } else {
        int div = c.max_len + width;
        float threshold_time;
        if (div != 0)
            threshold_time = c.progress - c.duration * (1 - width / float(div));
        else
            threshold_time = c.progress - c.duration;
        while (row < row_max && res < c.part_size) {
            if (target_row != rows[c.mode][row]) {
                target_row = rows[c.mode][row];
                if (target_row != nullptr) {
                    div = target_row->max_len + width;
                    if (div != 0 && (target_row->progress > threshold_time ||
                                    target_row->progress + target_row->max_len * target_row->duration / div > c.progress))
                        break;
                }
            }
            row++;
            res++;
        }
    }
    return res;
}

vector<float> get_zoom_factor(vector<int>& source_size, vector<int>& target_size) {
    float source_aspect = float(source_size[0]) / source_size[1];
    float target_aspect = float(target_size[0]) / target_size[1];
    if (target_aspect < source_aspect) {  // narrower
        if (source_size[0] == 0 || source_aspect == 0) return {1, 0, 0};
        float scale_factor = float(target_size[0]) / source_size[0];
        return {scale_factor, 0, (target_size[1] - target_size[0] / source_aspect) / 2};
    } else if (target_aspect > source_aspect) {  // wider
        if (source_size[1] == 0) return {1, 0, 0};
        float scale_factor = target_size[1] / source_size[1];
        return {scale_factor, (target_size[0] - target_size[1] * source_aspect) / 2, 0};
    } else {
        if (source_size[0] == 0) return {1, 0, 0};
        return {float(target_size[0]) / source_size[0], 0, 0};
    }
}

// https://aegi.vmoe.info/docs/3.0/ASS_Tags/#index1h2
string ass_escape(string s) {
    const string ZERO_WIDTH_SPACE = "\xe2\x80\x8b"; // U+200B

    // prevent "\" from causing line breaks/escaping anything ("\\" won't work)
    string s2 = boost::replace_all_copy(s, R"(\)", R"(\)" + ZERO_WIDTH_SPACE);

    // escape "}" and "{" (override block chars) with backslash
    s2 = std::regex_replace(s2, std::regex(R"(([}{]))"), R"(\$1)");

    // preserve intended spacing at start and end of lines
    boost::replace_all(s2, "\n", ZERO_WIDTH_SPACE + R"(\N)" + ZERO_WIDTH_SPACE);
    return ZERO_WIDTH_SPACE + s2 + ZERO_WIDTH_SPACE;
}

string convert_color(int RGB) {
    if (RGB == 0x000000)
        return "000000";
    if (RGB == 0xFFFFFF)
        return "FFFFFF";
    int R = (RGB >> 16) & 0xFF;
    int G = (RGB >> 8) & 0xFF;
    int B = RGB & 0xFF;
    return fmt::format("{:02X}{:02X}{:02X}", B, G, R);
}

string convert_alpha(float alpha) {
    if (alpha <= 0.0)
        return "FF";
    if (alpha >= 1.0)
        return "00";
    return fmt::format("{:02X}", int(round((1.0 - alpha) * 255.0)));
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

class Ass {
public:
    int width;
    int height;
    int reserve_blank;
    string font_face;
    float font_size;
    float alpha;
    float duration_marquee;
    float duration_still;
    string filter;
    bool reduced;
    bool bold;
    bool live;
    // others
    vector<Comment> comments;
    unordered_map<string, string> fonts;
    vector<string> keys = {"defont", "mincho", "gothic"};
    vector<int> bili_player_size;
    vector<float> zoom_factor;
    string head;
    string body = "";
    bool need_clear = false;

    Ass(int w, int h, int rb, const string& ff, float fs, float a, float dm, float ds, const string& flt, bool rd, bool b, bool lv) :
            width(w), height(h), reserve_blank(rb), font_face(ff), font_size(fs), alpha(a), duration_marquee(dm),
            duration_still(ds), filter(flt), reduced(rd), bold(b), live(lv) {
        vector<string> fontlist;
        boost::split(fontlist, font_face, boost::is_any_of(","));
        font_face = fontlist[0];
        fontlist.resize(keys.size(), fontlist[0]);
        for (size_t i = 0; i < keys.size(); ++i) {
            fonts[keys[i]] = fontlist[i];
        }
        head = fmt::format("[Script Info]\n"
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
                           "YCbCr Matrix: None\n"
                           "\n"
                           "[V4+ Styles]\n"
                           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
                           // todo stylid
                           "Style: danmakuC, {2}, {3:.0f}, &H{4}FFFFFF, &H{4}FFFFFF, &H{4}000000, &H{4}000000, {5}, 0, 0, 0, 100, 100, 0.00, 0.00, 1, {6:.0f}, 0, 7, 0, 0, 0, 0\n"
                           "\n"
                           "[Events]\n"
                           "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n",
                           width, height, font_face, font_size, convert_alpha(alpha),
                           bold? -1:0, max(font_size / 25.0, 1.0));
        // bili_player_size = {512, 384}  // Bilibili player version 2010
        // bili_player_size = {540, 384}  // Bilibili player version 2012
        // bili_player_size = {672, 438}  // Bilibili player version 2014
        bili_player_size = {891, 589};    // Bilibili player version 2021 (flex)
        vector<int> target_size{width, height};
        zoom_factor = get_zoom_factor(bili_player_size, target_size);
    }

    bool add_comment(float progress, int ctime, const string& content, float size_factor, int mode, int color, int pool) {
        // need clear
        need_clear = true;
        // content regex filter
        if (filter != "" && regex_search(content, regex(filter)))
            return false;
        
        float duration = (mode == 1 || mode == 2)? duration_still : duration_marquee;
        Comment comment = Comment(progress, duration, ctime, content, mode, pool,
                                font_face, font_size * size_factor, color, alpha);

        // ASS renders typically ignore tab characters
        const string FULL_WIDTH_SPACE = "\xe3\x80\x80"; // U+3000
        boost::replace_all(comment.content, "\t", FULL_WIDTH_SPACE + FULL_WIDTH_SPACE);

        // calculate extra filed
        if (comment.mode != 4) {
            vector<string> parts;
            boost::split(parts, comment.content, boost::is_any_of("\n"));
            comment.lines = parts.size();
            comment.part_size = comment.size * comment.lines;
            int max_len = 0;
            for (string& p: parts) {
                int part_len = utf8_len(p);
                if (part_len > max_len)
                    max_len = part_len;
            }
            comment.max_len = max_len * comment.size;
        } else
            // bilipos comment
            comment.size = 25.0 * size_factor, comment.part_size = 0, comment.max_len = 0;
        comment.content = ass_escape(comment.content);
        comments.push_back(comment);
        return true;
    }

    bool add_nico_comment(float progress, float duration, int ctime, const string& content, float size_factor, int mode, int color,
                        float alpha_factor, string font, int pool, bool full, bool ender) {
        // need clear
        need_clear = true;
        // content regex filter
        if (filter != "" && regex_search(content, regex(filter)))
            return false;
        
        Comment comment = Comment(progress, duration, ctime, content, mode, pool,
                                fonts[font], font_size * size_factor, color, log2(1 + alpha) * alpha_factor);
        // ASS renders typically ignore tab characters
        const string FULL_WIDTH_SPACE = "\xe3\x80\x80"; // U+3000
        boost::replace_all(comment.content, "\t", FULL_WIDTH_SPACE + FULL_WIDTH_SPACE);

        // calculate extra filed
        vector<string> parts;
        boost::split(parts, comment.content, boost::is_any_of("\n"));
        comment.lines = parts.size();
        comment.part_size = comment.size * comment.lines;
        int max_len = 0;
        for (string& p: parts) {
            int part_len = utf8_len(p);
            if (part_len > max_len)
                max_len = part_len;
        }
        comment.max_len = max_len * comment.size;
        //resize
        comment.resize(height, full, ender);
        // retime
        if (mode == 0 || mode == 3)
            comment.retime(width, height, duration_marquee);
        comment.content = ass_escape(comment.content);
        comments.push_back(comment);
        return true;
    }

    string to_string() {
        if (body == "" || need_clear) {
            write_comments();
        }
        return head + body;
    }

    void write_comments(std::ofstream* out_fp = nullptr) {
        /// 1. clear body first
        body = "";
        /// 2. sort before find row
        stable_sort(comments.begin(), comments.end(), [](const Comment& a, const Comment& b) -> bool {
            if (a.vpos != b.vpos)
                return a.vpos < b.vpos;
            else
                return a.ctime < b.ctime;
        });
        /// 3. find row
        vector<vector<vector<Comment*>>> rows(4, vector<vector<Comment*>>(4, vector<Comment*>(height - reserve_blank + 1, nullptr)));
        for (size_t idx = 0; idx < comments.size(); ++idx) {
            Comment& c = comments[idx];
            if (c.mode != 4) {  // not a bilipos
                int row = 0;
                int row_max = height - reserve_blank - c.part_size;
                // Keep the row value fixed if the partsize exceeds stage height
                // https://w.atwiki.jp/commentart2/pages/31.html ③高さ固定
                if (row_max <= 0) {
                    if (c.mode == 0 || c.mode == 3) {
                        c.row = (height - reserve_blank) / 2;
                        c.align = 4;
                    } else
                        c.row = 0;
                }
                else {
                    bool flag = true;
                    while (row <= row_max) {
                        int free_row = test_free_row(rows[c.pool], c, row,
                                                    width, height, reserve_blank);
                        if (free_row >= c.part_size) {
                            mark_comment_row(rows[c.pool], c, row);
                            flag = false;
                            break;
                        } else
                            row += free_row || 1; // todo condition is always true?
                    }
                    if (flag) {
                        if (reduced) continue;
                        row = find_alternative_row(rows[c.pool], c, height, reserve_blank);
                        if (row == 0)
                            unmark_rows(rows[c.pool], c.mode);
                        mark_comment_row(rows[c.pool], c, row);
                    }
                    c.row = row;
                }
                write_comment(c, out_fp);
            } else
                write_bilipos_comment(c, out_fp);
        }
        need_clear = false;
    }

    void write_comment(Comment& c, std::ofstream* out_fp = nullptr) {
        vector<string> styles;
        switch (c.mode) {
            case 1: {
                if (c.lines > 1)
                    styles.push_back(fmt::format("\\pos({:.0f}, {})",
                                             (width - c.max_len) / 2, c.row));
                else
                    styles.push_back(fmt::format("\\an8\\pos({}, {})",
                                             width / 2, c.row));
                break;
            }
            case 2: {
                if (c.lines > 1)
                    styles.push_back(fmt::format("\\an1\\pos({:.0f}, {})",
                                             (width - c.max_len) / 2, convert_type2(c.row, height, reserve_blank)));
                else
                    styles.push_back(fmt::format("\\an2\\pos({}, {})",
                                             width / 2, convert_type2(c.row, height, reserve_blank)));
                break;
            }
            case 3: {
                if (c.align == 4)
                    styles.push_back("\\an4");
                styles.push_back(fmt::format("\\move({2:.0f}, {1}, {0}, {1})",
                                             width, c.row, c.delta_l - c.max_len));
                break;
            }
            default: {
                if (c.align == 4)
                    styles.push_back("\\an4");
                styles.push_back(fmt::format("\\move({0:.0f}, {1}, {2}, {1})",
                                             width - c.delta_l, c.row, -c.max_len));
            }
        }
        if (c.font != font_face) {
            styles.push_back(fmt::format("\\fn{}", c.font));
            if (bold) styles.push_back("\\b0");
        }
        float size = c.size - font_size;
        if (size <= -1 || size >= 1)
            styles.push_back(fmt::format("\\fs{:.0f}", c.size));
        if (c.color != 0xFFFFFF) {
            styles.push_back(fmt::format("\\c&H{}&", convert_color(c.color)));
            if (c.color == 0x000000)
                styles.push_back("\\3c&H666666&");
        }
        if (c.alpha != alpha) {
            styles.push_back(fmt::format("\\alpha&H{}&", convert_alpha(c.alpha)));
        }
        string line = fmt::format("Dialogue: 2,{0},{1},danmakuC,,0000,0000,0000,,{{{2}}}{3}\n",
                                  convert_progress(c.progress),
                                  convert_progress(c.progress + c.duration),
                                  boost::algorithm::join(styles, ""),
                                  c.content
        );
        if (out_fp == nullptr)
            body += line;
        else
            *out_fp << line;
    }

    void write_bilipos_comment(Comment& c, std::ofstream* out_fp = nullptr) {
        // todo
        return;
    }

    float get_position(float input_pos, bool is_height) {
        if (input_pos > 1)
            return zoom_factor[0] * input_pos + zoom_factor[is_height + 1];
        else
            return bili_player_size[is_height] * zoom_factor[0] * input_pos + zoom_factor[is_height + 1];
    }

    void write_to_file(string out_filename) {
        std::ofstream out_fp;
        out_fp.open(out_filename, std::ofstream::out);
        out_fp << head;
        write_comments(&out_fp);
        out_fp.close();
    }
};

namespace py = pybind11;

PYBIND11_MODULE(ass, m) {
    m.doc() = "pybind11 ass extension"; // optional module docstring
    py::class_<Ass>(m, "Ass")
            .def(py::init<int, int, int, const string&, float, float, float, float, string, bool, bool, bool>())
            .def("add_comment", &Ass::add_comment)
            .def("add_nico_comment", &Ass::add_nico_comment)
            .def("to_string", &Ass::to_string)
            .def("write_to_file", &Ass::write_to_file);
}
