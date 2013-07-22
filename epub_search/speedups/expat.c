/*
 * epub-search - ePub content searching program
 * Copyright (C) 2013 Garrett Regier
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 */

#define PY_SSIZE_T_CLEAN 1
#include "Python.h"

#include "stdio.h"

#include "expat.h"


typedef struct {
    int buffer_len;
    char *buffer;
    XML_Parser parser;
} StripTagsState;


static inline void
strip_tags_state_append_data (StripTagsState *state,
                              const XML_Char *data,
                              int len)
{
    /* Using memmove as the buffer and data might overlap */
    Py_MEMCPY(state->buffer, data, len * sizeof(XML_Char));

    state->buffer += len;
    state->buffer_len += len;
}

static void
strip_tags_CharacterDataHandler(void *user_data,
                                const XML_Char *data,
                                int len)
{
    StripTagsState *state = user_data;

    strip_tags_state_append_data(state, data, len);
}

static void
strip_tags_EndElementHandler(void *user_data,
                             const XML_Char *name)
{
    StripTagsState *state = user_data;

    /* Really this should be expanded to ignore script and style elements */

    if (strcmp(name, "p") == 0 ||
        strcmp(name, "div") == 0 ||
        strcmp(name, "br") == 0 ||
        (name[0] == 'h' && name[1] >= '1' && name[1] <= '6' &&
         name[2] == '\0')) {

        strip_tags_state_append_data(state, "\n", strlen("\n"));
    }
}

static void
strip_tags_StartElementHandler(void *user_data,
                               const XML_Char *name,
                               const XML_Char *atts[])
{
    StripTagsState *state = user_data;

    if (strcmp(name, "body") != 0)
        return;

    XML_SetCharacterDataHandler(state->parser,
                                strip_tags_CharacterDataHandler);
    XML_SetEndElementHandler(state->parser, strip_tags_EndElementHandler);
    XML_SetStartElementHandler(state->parser, NULL);
}

static PyObject *
py_expat_strip_tags(PyObject *self,
                    PyObject *args)
{
    PyObject *xhtml, *text;
    StripTagsState state;
    int success;

    if (!PyArg_ParseTuple(args, "S", &xhtml))
        return NULL;

    /* The text can never be bigger than the XHTML, so
     * over allocate instead of growing multiple times.
     *
     * This assumes that XML_Char is 8-bit, and hence in UTF-8.
     */
    text = PyString_FromStringAndSize(NULL, PyString_GET_SIZE(xhtml));
    if (text == NULL)
        return PyErr_NoMemory();

    Py_BEGIN_ALLOW_THREADS

    state.buffer = PyString_AS_STRING(text);
    state.buffer_len = 0;

    state.parser = XML_ParserCreate(NULL);
    XML_SetUserData(state.parser, (void *) &state);

    XML_SetStartElementHandler(state.parser, strip_tags_StartElementHandler);

    /* Parse the buffer which will be transformed into the content */
    success = XML_Parse(state.parser, PyString_AS_STRING(xhtml),
                        PyString_GET_SIZE(xhtml), 1);

    XML_ParserFree(state.parser);

    Py_END_ALLOW_THREADS

    if (success) {
        /* Don't use memory that we don't need */
       _PyString_Resize(&text, state.buffer_len);
    } else {
        Py_DECREF(text);
        PyErr_SetString(PyExc_ValueError, "Invalid XHTML");
        return NULL;
    }

    return text;
}


static PyMethodDef speedups_expat_methods[] = {
    { "strip_tags",  py_expat_strip_tags, METH_VARARGS,
      "Strips the tags from the XHTML string."},
    { NULL, NULL, 0, NULL}
};

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "epub_search._speedups_expat",        /* m_name */
    NULL,                                 /* m_doc */
    -1,                                   /* m_size */
    speedups_expat_methods,               /* m_methods */
    NULL,                                 /* m_reload */
    NULL,                                 /* m_traverse */
    NULL,                                 /* m_clear*/
    NULL,                                 /* m_free */
};
#endif

PyObject *
moduleinit(void)
{
    PyObject *module;

#if PY_MAJOR_VERSION >= 3
    module = PyModule_Create(&moduledef);
#else
    module = Py_InitModule("epub_search._speedups_expat",
                           speedups_expat_methods);
#endif

    return module;
}

#if PY_MAJOR_VERSION >= 3
PyMODINIT_FUNC
PyInit_speedups_expat(void)
{
    return moduleinit();
}
#else
void
init_speedups_expat(void)
{
    moduleinit();
}
#endif

/* ex:set ts=4 et: */
