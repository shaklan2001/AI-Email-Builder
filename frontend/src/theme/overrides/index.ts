import merge from "lodash/merge";
import type { Theme } from "@mui/material/styles";
import { defaultProps } from "./default-props";
import { accordion } from "./components/accordion";
import { alert } from "./components/alert";
import { appBar } from "./components/appbar";
import { autocomplete } from "./components/autocomplete";
import { avatar } from "./components/avatar";
import { badge } from "./components/badge";
import { breadcrumbs } from "./components/breadcrumbs";
import { button } from "./components/button";
import { buttonGroup } from "./components/button-group";
import { card } from "./components/card";
import { checkbox } from "./components/checkbox";
import { chip } from "./components/chip";
import { cssBaseline } from "./components/css-baseline";
import { dialog } from "./components/dialog";
import { drawer } from "./components/drawer";
import { fab } from "./components/fab";
import { list } from "./components/list";
import { menu } from "./components/menu";
import { pagination } from "./components/pagination";
import { paper } from "./components/paper";
import { popover } from "./components/popover";
import { progress } from "./components/progress";
import { radio } from "./components/radio";
import { rating } from "./components/rating";
import { select } from "./components/select";
import { skeleton } from "./components/skeleton";
import { slider } from "./components/slider";
import { stepper } from "./components/stepper";
import { svgIcon } from "./components/svg-icon";
import { switches } from "./components/switch";
import { table } from "./components/table";
import { tabs } from "./components/tabs";
import { textField } from "./components/textfield";
import { toggleButton } from "./components/toggle-button";
import { tooltip } from "./components/tooltip";
import { typography } from "./components/typography";

export function componentsOverrides(theme: Theme) {
  return merge(
    defaultProps(theme),
    fab(theme),
    tabs(theme),
    chip(theme),
    card(theme),
    menu(theme),
    list(theme),
    badge(theme),
    table(theme),
    paper(theme),
    alert(theme),
    radio(theme),
    select(theme),
    button(theme),
    rating(theme),
    dialog(theme),
    appBar(theme),
    avatar(theme),
    slider(theme),
    drawer(theme),
    stepper(theme),
    tooltip(theme),
    popover(theme),
    svgIcon(theme),
    switches(theme),
    checkbox(theme),
    skeleton(theme),
    progress(theme),
    textField(theme),
    accordion(theme),
    typography(theme),
    pagination(theme),
    buttonGroup(theme),
    breadcrumbs(theme),
    cssBaseline(theme),
    autocomplete(theme),
    toggleButton(theme),
  );
}
