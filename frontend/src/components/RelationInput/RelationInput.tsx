import React from "react";
import {Button, Form, Input, Select} from "antd";
import {Aspect, Entity, Relation} from "../../services/metaModelService";
import TextArea from "antd/es/input/TextArea";


export interface Props {
    entities: Entity[];
    relation: Partial<Relation>;
    onChange: (e: Partial<Relation>) => void;
    onSubmit: (e: Relation) => void;
}

const RelationInput = ({relation, entities, onChange, onSubmit}: Props) => {
    return (
        <Form>
            <Form.Item>New Relation</Form.Item>
            <Form.Item label={"name"}>
                <Input value={relation.name} onChange={(e) => {
                    onChange({
                        ...relation,
                        name: e.target.value
                    })
                }}/>
            </Form.Item>
            <Form.Item label={"description"}>
                <TextArea value={relation.description} onChange={(e) => {
                    onChange({
                        ...relation,
                        description: e.target.value
                    })
                }}/>
            </Form.Item>
            <Form.Item label={"source"}>
                <Select
                    onChange={(_, option) => {
                        if(Array.isArray(option)) {
                            throw Error();
                        }
                        onChange({
                            ...relation,
                            source: option.entity
                        })
                    }}
                >
                    {entities.map(e => <Select.Option value={e.name} entity={e}>{e.name}</Select.Option>)}
                </Select>
            </Form.Item>
            <Form.Item label={"target"}>
                <Select
                    onChange={(_, option) => {
                        if(Array.isArray(option)) {
                            throw Error();
                        }
                        onChange({
                            ...relation,
                            target: option.entity
                        })
                    }}
                >
                    {entities.map(e => <Select.Option value={e.name} entity={e}>{e.name}</Select.Option>)}
                </Select>
            </Form.Item>
            <Form.Item>
                <Button
                    type={"primary"}
                    onClick={() => {
                        if(!relation.description) return;
                        if(!relation.name) return;
                        if(!relation.source) return;
                        if(!relation.target) return;
                        onSubmit({
                            name: relation.name,
                            description: relation.description,
                            source: relation.source,
                            target: relation.target
                        });
                    }}
                >
                    Create
                </Button>
            </Form.Item>
        </Form>
    );
}

export default RelationInput;