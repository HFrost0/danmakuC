#ifndef DANMAKUC_ASS_H

#define DANMAKUC_ASS_H

#include <map>
#include <pybind11/pybind11.h>
#include <pybind11/stl_bind.h>

namespace py = pybind11;


class Comment {
public:
    float progress;
    int ctime;
    std::string content;
    float font_size;
    int mode;
    int color;
    // others
    float size;
    float part_size;
    float max_len;
    int row;

    Comment() = delete;

    Comment(float progress,
            int ctime,
            std::string content,
            float font_size,
            int mode,
            int color
    ) : progress(progress), ctime(ctime), mode(mode), content(content), color(color), font_size(font_size) {}
};


std::string comments2ass(std::vector<Comment>& comments,
                         int width,
                         int height,
                         int reserve_blank,
                         std::string font_face,
                         float font_size,
                         float alpha,
                         float duration_marquee,
                         float duration_still,
                         bool reduced);

PYBIND11_MAKE_OPAQUE(std::vector<Comment>);
PYBIND11_MODULE(ass, m) {
    m.doc() = "pybind11 ass plugin"; // optional module docstring

    py::bind_vector<std::vector<Comment>>(m, "VectorComment");

    py::class_<Comment>(m, "Comment")
            .def(py::init<float , int, std::string, float , int, int>())
            .def("__repr__", [](const Comment& c) {
                return "<Comment '" + c.content + "'>";
            });
    m.def("comments2ass", &comments2ass, "convert comments to ass");
}

#endif //DANMAKUC_ASS_H
