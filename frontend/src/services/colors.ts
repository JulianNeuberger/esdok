import {AssertionError} from "assert";

export const hsvToRgb = (h: number, s: number, v: number) => {
    let r = 0;
    let g = 0;
    let b = 0;

    const i = Math.floor(h * 6);
    const f = h * 6 - i;
    const p = v * (1 - s);
    const q = v * (1 - f * s);
    const t = v * (1 - (1 - f) * s);

    switch (i % 6) {
        case 0: [r, g, b] = [v, t, p]; break;
        case 1: [r, g, b] = [q, v, p]; break;
        case 2: [r, g, b] = [p, v, t]; break;
        case 3: [r, g, b] = [p, q, v]; break;
        case 4: [r, g, b] = [t, p, v]; break;
        case 5: [r, g, b] = [v, p, q]; break;
        default: throw new Error();

    }

    return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}

export const toHex = (r: number, g: number, b: number): string => {
    const componentToHex = (c: number) => {
        let hex = c.toString(16);
        return hex.length == 1 ? "0" + hex : hex;
    }

    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}

export const randomColorScheme = () => {
    const hue = Math.random();
    const [textR, textG, textB] = hsvToRgb(hue, .8, .4);
    const [backR, backG, backB] = hsvToRgb(hue, .3, .9);
    return {
        "textColor": toHex(textR, textG, textB),
        "backgroundColor": toHex(backR, backG, backB)
    }
}