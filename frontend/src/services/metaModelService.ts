export interface Color {
    r: number;
    g: number;
    b: number;
    hex: string;
}

export interface Aspect {
    name: string;
    textColor: Color;
    shapeColor: Color;
    shape: string;
}

export interface Entity {
    name: string;
    description: string;
    aspect: Aspect;
    position: {
        x: number,
        y: number
    }
}

export interface Relation {
    name: string;
    description: string;
    source: Entity;
    target: Entity;
}

export interface MetaModel {
    entities: Entity[];
    relations: Relation[];
}

export class MetaModelService {

    public constructor() {

    }

    public loadAspects = async (): Promise<Aspect[] | undefined> => {
        const response = await fetch(" http://127.0.0.1:5000/model/aspect");
        return await response.json();
    }

    public patchModel = async (entities: Entity[], relations: Relation[]): Promise<boolean> => {
        const response = await fetch("http://127.0.0.1:5000/model/", {
            method: "PATCH",
            body: JSON.stringify({
                "entities": entities,
                "relations": relations,
            }),
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
        });
        const json = await response.json();
        return json["success"];
    }

    public loadModel = async (): Promise<MetaModel | undefined> => {
        const response = await fetch("http://127.0.0.1:5000/model/");
        const json = await response.json();
        if(!Object.hasOwn(json, "entities")) {
            return undefined;
        }
        if(!Object.hasOwn(json, "relations")) {
            return undefined;
        }
        return json;
    }
}