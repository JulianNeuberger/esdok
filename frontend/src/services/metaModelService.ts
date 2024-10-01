export interface Aspect {
    name: string;
}

export interface Entity {
    name: string;
    description: string;
    aspect: Aspect;
}

export interface Relation {
    name: string;
    description: string;
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

    public addToModel = async (entities: Entity[], relations: Relation[]): Promise<boolean> => {
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

        /*return {
            nodes: [
                {id: "n1", name: "Martin K.", aspect: "organizational"},
                {id: "n2", name: "Julian N.", aspect: "organizational"},
                {id: "n3", name: "Uni Bayreuth", aspect: "organizational"},
                {id: "n4", name: "TU Wien", aspect: "organizational"},
                {id: "n5", name: "Stefan B.", aspect: "organizational"},
            ],
            edges: [
                {id: "e1", sourceId: "n1", targetId: "n3", name: "employed at"},
                {id: "e2", sourceId: "n2", targetId: "n3", name: "employed at"},
                {id: "e3", sourceId: "n5", targetId: "n4", name: "employed at"},
                {id: "e4", sourceId: "n3", targetId: "n4", name: "cooperate"},
            ],
        }*/
    }
}