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
    shape: "rect" | "parallelogram" | "rounded" | undefined;
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

    public listMetaModels = async (): Promise<string[]> => {
        const response = await fetch(` http://127.0.0.1:5000/model/`);
        return await response.json();
    }

    public loadAspects = async (name: string): Promise<Aspect[]> => {
        const response = await fetch(` http://127.0.0.1:5000/model/${name}/aspect`);
        return await response.json();
    }

    public patchModel = async (name: string, entities: Entity[], relations: Relation[]): Promise<boolean> => {
        const response = await fetch(`http://127.0.0.1:5000/model/${name}/`, {
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

    public loadModel = async (name: string): Promise<MetaModel | undefined> => {
        const response = await fetch(`http://127.0.0.1:5000/model/${name}/`);
        const json = await response.json();
        if(!Object.hasOwn(json, "entities")) {
            return undefined;
        }
        if(!Object.hasOwn(json, "relations")) {
            return undefined;
        }
        return json;
    }

    public extract = async (name: string, file: File): Promise<boolean> => {
        const data = new FormData();
        data.append("file", file);

        const response = await fetch(` http://127.0.0.1:5000/model/${name}/extract`, {
            method: "POST",
            body: data
        });

        const json = await response.json();
        return json["success"];
    }
}