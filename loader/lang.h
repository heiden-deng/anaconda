/*
 * lang.h
 *
 * Copyright (C) 2007  Red Hat, Inc.  All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#ifndef _LANG_H_
#define _LANG_H_

#include "loader.h"

#define _(x) translateString (x)
#define N_(foo) (foo)

struct langInfo {
    char * lang, * key, * lc_all, * keyboard;
    unsigned int text_supported;
} ;


int chooseLanguage(char ** lang);
char * translateString(char * str);
int setLanguage (const char * key, int forced);
int getLangInfo(struct langInfo **langs);
char * normalizeLang(const char *s);

extern const char *LANG_DEFAULT;

#endif /* _LANG_H_ */